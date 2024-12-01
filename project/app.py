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

            def table_for(jobs):
                if not jobs:
                    return [["No jobs available", "", "", "", ""]]  # Placeholder for empty table
                return [
                    [
                        job.title,
                        job.company,
                        job.location,
                        ", ".join(job.skills),
                        job.url
                    ]
                    for job in jobs
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


            def get_interview_details(job):
                """
                Fetch detailed interview preparation data for the selected job.
                """
                # Example structure of returned data
                return {
                    "technical_questions": [
                        {"question": "What is a REST API?", "answer": "A REST API is ..."},
                        {"question": "Explain database optimization.", "answer": "Database optimization involves ..."}
                    ],
                    "behavioral_questions": [
                        {"question": "Tell me about a time you worked in a team.", "answer": "In my previous role ..."}
                    ]
                }


            def display_interview_details(selected_job):
                details = get_interview_details(selected_job)
            
                technical = "\n".join(
                    [f"**Q: {q['question']}**\nA: {q['answer']}" for q in details["technical_questions"]]
                )
                behavioral = "\n".join(
                    [f"**Q: {q['question']}**\nA: {q['answer']}" for q in details["behavioral_questions"]]
                )
                
                return f"""
                ### Technical Questions
                {technical}
            
                ### Behavioral Questions
                {behavioral}
                """


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

            def do_select(selected_index: gr.SelectData):
                # Retrieve the current job memory
                jobs = self.get_agent_framework().memory
            
                # Validate if jobs list is non-empty
                if not jobs:
                    return "No jobs are available to select."
            
                # Validate the selected index
                row = selected_index.index[0]
                if row < 0 or row >= len(jobs):
                    return f"Invalid selection. Please select a valid job index (0 to {len(jobs)-1})."
            
                # Fetch the selected job and process it
                selected_job = jobs[row]
                details = display_interview_details(selected_job)
                self.get_agent_framework().planner.messenger.alert(selected_job)
                return details


            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:24px"><strong>Job Insights</strong> - Your personalized job recommendation platform</div>')
            with gr.Row():
                with gr.Column(scale=3):
                    jobs_table = gr.Dataframe(
                            value=[["No jobs available", "", "", "", ""]],
                            headers=["Job Title", "Company", "Location", "Skills", "URL"],
                            wrap=True,
                            column_widths=[2, 1, 1, 2, 2],
                            row_count=10,
                            col_count=5,
                            max_height=400,
                        )

                with gr.Column(scale=2):
                    interview_details = gr.Markdown(value="", label="Interview Preparation")
            with gr.Row():
                with gr.Column(scale=1):
                    logs = gr.HTML()
                
            
            
            jobs_table.select(do_select,outputs=interview_details)

            ui.load(run_with_logging, inputs=[log_data], outputs=[log_data, logs, jobs_table])


            ui.launch(share=False, inbrowser=True)

if __name__ == "__main__":
    App().run()
