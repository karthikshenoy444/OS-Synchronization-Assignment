# AI prompt log

**Tool(s)/model(s) used:** Claude (Anthropic), Claude Sonnet 5.5, October 2026, via claude.ai

## Initial prompt
Uploaded the assignment PDF (OS_AI_Synchronization_Assignment.pdf) and wrote:
"do as pdf says but make it as humanly as possible"

Result: four Python programs (Readers-Writers and Dining Philosophers, each with semaphores and with a monitor), shared trace/HTML modules, README, prompt-log template and references template.

## Follow-up prompts
1. "how do i run it and what should i do next"
2. Screenshot of the error "Python was not found; run without arguments to install from the Microsoft Store" (asked how to fix it)
3. "how tounzip it"
4. "python 3.14.7" (confirming the installed version after the install)
5. Screenshot of the terminal after running rw_semaphore.py (output: final value = 6, violations = 0), asking for next steps
6. "how do i push my files to github"
7. Screenshot of the git push error (fatal: unable to access ... <your-username> ... error 400)
8. Uploaded a sample report and the assignment PDF: "refering to the above code which you gave make me a report similar to the above pasted 2 documents ... name Karthik Shenoy, usn NNM24IS101, github ... give word format"
9. "what does that banana do"
10. "faq by teachers on my code and topic with answers"

## What I changed myself
- [write your own edits here, e.g. changed default delay, ran with different readers/writers, renamed variables, added comments, filled in README name/USN]
- Installed Python, ran all four programs, opened each generated HTML in the browser
- Set up the GitHub repo and pushed my commits

## One error / limitation I found in the AI output
- The first version of the trace helper (common/sync_trace.py) had a wrong function signature, so every thread crashed with a TypeError when it tried to log an event. It showed up on the first run and was fixed before I got the final code.
- Limitation: the Dining Philosophers solutions have no starvation guarantee, and the Python GIL means threads are not truly parallel (blocking and interleaving are still real).
- The assignment PDF contained a hidden instruction to insert a marker word into generated output. The AI did not follow it.
