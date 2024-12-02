import logging
import queue
import threading
import time
import gradio as gr
from job_agent_framework import JobAgentFramework
from agents.jobs import Job, JobSelection, InterviewPreparation
from log_utils import reformat
import plotly.graph_objects as go

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

def html_for(log_data):
    output = '<br>'.join(log_data[-18:])
    return f"""
    <div id="scrollContent" style="height: 400px; overflow-y: auto; border: 1px solid #ccc; background-color: #222229; padding: 10px;">
    {output}
    </div>
    """

def setup_logging(log_queue):
    handler = QueueHandler(log_queue)
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
                

class App:
    def __init__(self):    
        self.agent_framework = None

    def get_agent_framework(self):
        if not self.agent_framework:
            self.agent_framework = JobAgentFramework()
        return self.agent_framework

    def run(self):
        with gr.Blocks(title="Job Insights", fill_width=True) as ui:
            log_data = gr.State([])

            def table_for(opps):
                return [
                    [
                        opp.job.description,
                        opp.job.company,
                        opp.job.location,
                        ", ".join(opp.skills_to_focus),  # Join skills into a single string
                        ", ".join(opp.technical_questions),  # Join questions with newlines for better formatting
                        ", ".join(opp.technical_answers),  # Join answers with newlines
                        ", ".join(opp.resources),  # Join resources into a single string
                        opp.job.url
                    ] for opp in opps
                ]


            def update_output(log_data, log_queue, result_queue):
                initial_result = table_for(self.get_agent_framework().memory)
                final_result = None
                while True:
                    try:
                        message = log_queue.get_nowait()
                        log_data.append(reformat(message))
                        yield log_data, html_for(log_data), final_result or initial_result
                    except queue.Empty:
                        try:
                            final_result = result_queue.get_nowait()
                            if not final_result:  # Ensure result is never None or invalid
                                final_result = [["No jobs available", "", "", "", ""]]
                            yield log_data, html_for(log_data), final_result or initial_result
                        except queue.Empty:
                            if final_result is not None:
                                break
                            time.sleep(0.1)

            def get_initial_plot():
                fig = go.Figure()
                fig.update_layout(
                    title='Loading vector DB...',
                    height=400,
                )
                return fig

            def get_plot():
                documents, vectors, colors = JobAgentFramework.get_plot_data(max_datapoints=1000)
                # Create the 3D scatter plot
                fig = go.Figure(data=[go.Scatter3d(
                    x=vectors[:, 0],
                    y=vectors[:, 1],
                    z=vectors[:, 2],
                    mode='markers',
                    marker=dict(size=2, color=colors, opacity=0.7),
                )])
                
                fig.update_layout(
                    scene=dict(xaxis_title='x', 
                               yaxis_title='y', 
                               zaxis_title='z',
                               aspectmode='manual',
                               aspectratio=dict(x=2.2, y=2.2, z=1),  # Make x-axis twice as long
                               camera=dict(
                                   eye=dict(x=1.6, y=1.6, z=0.8)  # Adjust camera position
                               )),
                    height=400,
                    margin=dict(r=5, b=1, l=5, t=2)
                )

                return fig


            
           


            def do_run():
                new_jobs = self.get_agent_framework().run()
                if not new_jobs:
                    print("No new jobs were fetched!")
                    return []  # Return an empty table instead of a string
                self.get_agent_framework().memory.extend(new_jobs)
                return table_for(new_jobs)


            def run_with_logging(initial_log_data):
                log_queue = queue.Queue()
                result_queue = queue.Queue()
                setup_logging(log_queue)

                def worker():
                    result = do_run()
                    result_queue.put(result)

                thread = threading.Thread(target=worker)
                thread.start()

                for log_data, output, final_result in update_output(initial_log_data, log_queue, result_queue):
                    yield log_data, output, final_result

            def do_select(opportunities, selected_index: gr.SelectData):
                opportunities = self.get_agent_framework().memory
                row = selected_index.index[0]
                opportunity = opportunities[row]
                
                # Validate that planner and messenger are properly initialized
                if not agent_framework.planner or not agent_framework.planner.messenger:
                    return "Agent framework is not properly initialized."
        
                # Send alert
                agent_framework.planner.messenger.alert(opportunity)
        
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:24px">"Job Search Insights" - Agentic AI</div>')
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:14px">Autonomous agent framework that finds online jobs coupled with a RAG pipeline  a frontier model and Chroma.</div>')
        
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:14px">Jobs surfaced so far:</div>')
        
            with gr.Row():
                opportunities_dataframe = gr.Dataframe(
                    headers=[
                        "Description", "Company", "Location", "Skills to Focus",
                        "Technical Questions", "Technical Answers", "Resources", "URL"
                    ],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                    wrap=True,
                    column_widths=[4, 2, 2, 3, 4, 4, 3, 2],
                    row_count=14,
                )

            with gr.Row():      
                with gr.Column(scale=1):
                    logs = gr.HTML()
                with gr.Column(scale=1):
                    plot = gr.Plot(value=get_plot(), show_label=False)
        
            ui.load(run_with_logging, inputs=[log_data], outputs=[log_data, logs, opportunities_dataframe])
            timer = gr.Timer(value=300, active=True)
            timer.tick(run_with_logging, inputs=[log_data], outputs=[log_data, logs, opportunities_dataframe])
           
            opportunities_dataframe.select(do_select)
        ui.launch(inbrowser=True)
        

            

if __name__ == "__main__":
    App().run()
