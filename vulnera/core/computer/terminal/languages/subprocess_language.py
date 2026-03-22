import os
import queue
import re
import signal
import subprocess
import threading
import time
import traceback

from ..base_language import BaseLanguage


class SubprocessLanguage(BaseLanguage):
    def __init__(self):
        # Default start command for plain subprocess environments
        if os.name == "nt":
            self.start_cmd = ["cmd.exe"]
        else:
            self.start_cmd = [os.environ.get("SHELL", "bash")]

        self.process = None
        self.verbose = False
        self.output_queue = queue.Queue()
        self.done = threading.Event()
        # Fixed timeout values (not configurable by external caller)
        self.command_timeout = 300  # 5 minutes fixed command timeout
        self.total_timeout = 300  # 5 minutes max total operation timeout
        self._shutdown_event = threading.Event()
        self._active_threads = []

    def detect_active_line(self, line):
        return None

    def detect_end_of_execution(self, line):
        return None

    def line_postprocessor(self, line):
        return line

    def preprocess_code(self, code):
        """
        This needs to insert an end_of_execution marker of some kind,
        which can be detected by detect_end_of_execution.

        Optionally, add active line markers for detect_active_line.
        """
        return code

    def terminate(self):
        """Properly terminate the subprocess and clean up all resources."""
        self._shutdown_event.set()

        if self.process:
            try:
                # Send SIGTERM first
                self.process.terminate()

                # Wait up to 5 seconds for graceful shutdown
                try:
                    self.process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't respond
                    self.process.kill()
                    try:
                        self.process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        pass  # Give up

                # Close pipes
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                except:
                    pass
                try:
                    if self.process.stdout:
                        self.process.stdout.close()
                except:
                    pass
                try:
                    if self.process.stderr:
                        self.process.stderr.close()
                except:
                    pass

            except Exception as e:
                if self.verbose:
                    print(f"Error during process termination: {e}")
            finally:
                self.process = None

        # Clean up any remaining threads
        for thread in self._active_threads[:]:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self._active_threads.clear()

        # Clear queues and events
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break
        self.done.clear()
        self._shutdown_event.clear()

    def stop(self):
        """Stop current execution gracefully."""
        self._shutdown_event.set()

    def start_process(self):
        if self.process:
            self.terminate()

        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"

        try:
            self.process = subprocess.Popen(
                self.start_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                universal_newlines=True,
                env=my_env,
                encoding="utf-8",
                errors="replace",
                # Add session leadership to handle signals properly
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None,
            )

            # Start output handling threads
            stdout_thread = threading.Thread(
                target=self.handle_stream_output,
                args=(self.process.stdout, False),
                daemon=True,
                name="stdout_handler"
            )
            stderr_thread = threading.Thread(
                target=self.handle_stream_output,
                args=(self.process.stderr, True),
                daemon=True,
                name="stderr_handler"
            )

            self._active_threads.extend([stdout_thread, stderr_thread])
            stdout_thread.start()
            stderr_thread.start()

        except Exception as e:
            # Don't yield here - this method is not a generator
            raise RuntimeError(f"Failed to start process: {e}")

    def run(self, code):
        """Execute code with proper timeout, interrupt, and cleanup handling."""
        start_time = time.time()
        retry_count = 0
        max_retries = 3

        # Setup
        try:
            code = self.preprocess_code(code)
            if not self.process:
                self.start_process()
        except Exception as e:
            yield {
                "type": "console",
                "format": "output",
                "content": f"Setup failed: {traceback.format_exc()}",
            }
            return

        while retry_count <= max_retries:
            if self.verbose:
                print(f"(after processing) Running processed code:\n{code}\n---")

            self.done.clear()
            command_start = time.time()

            try:
                # Send command to process
                self.process.stdin.write(code + "\n")
                self.process.stdin.flush()

                # Wait for completion with timeout and interrupt handling
                while not self._shutdown_event.is_set():
                    # Check for total timeout
                    if time.time() - start_time > self.total_timeout:
                        yield {
                            "type": "console",
                            "format": "output",
                            "content": f"[TIMEOUT] Operation exceeded {self.total_timeout}s total timeout",
                        }
                        self.terminate()
                        return

                    # Check for command timeout
                    if time.time() - command_start > self.command_timeout:
                        yield {
                            "type": "console",
                            "format": "output",
                            "content": f"[TIMEOUT] Command exceeded {self.command_timeout}s timeout",
                        }
                        self.terminate()
                        return

                    # Yield any available output
                    try:
                        while not self.output_queue.empty():
                            output = self.output_queue.get_nowait()
                            yield output
                    except queue.Empty:
                        pass

                    # Check if command completed
                    if self.done.is_set():
                        # Drain remaining output
                        time.sleep(0.1)  # Brief pause for final output
                        while not self.output_queue.empty():
                            try:
                                output = self.output_queue.get_nowait()
                                yield output
                            except queue.Empty:
                                break
                        break

                    # Small sleep to prevent busy waiting
                    time.sleep(0.05)

                # Check if we were shutdown
                if self._shutdown_event.is_set():
                    yield {
                        "type": "console",
                        "format": "output",
                        "content": "[ABORTED] Operation aborted by user",
                    }
                    return

                break  # Success

            except KeyboardInterrupt:
                yield {
                    "type": "console",
                    "format": "output",
                    "content": "[ABORTED] Operation aborted by user (CTRL+C)",
                }
                self.terminate()
                return

            except Exception as e:
                if retry_count != 0:
                    yield {
                        "type": "console",
                        "format": "output",
                        "content": f"{traceback.format_exc()}\nRetrying... ({retry_count}/{max_retries})\nRestarting process.",
                    }

                self.terminate()
                self.start_process()

                retry_count += 1
                if retry_count > max_retries:
                    yield {
                        "type": "console",
                        "format": "output",
                        "content": "Maximum retries reached. Could not execute code.",
                    }
                    return

    def handle_stream_output(self, stream, is_error_stream):
        """Handle streaming output from subprocess with proper shutdown handling."""
        try:
            while not self._shutdown_event.is_set():
                # Use non-blocking read with timeout
                import select
                if hasattr(select, 'select') and hasattr(stream, 'fileno'):
                    try:
                        ready, _, _ = select.select([stream], [], [], 0.1)
                        if not ready:
                            continue
                    except (OSError, ValueError):
                        # select not available or stream not selectable
                        pass

                try:
                    line = stream.readline()
                    if not line:  # EOF
                        break

                    if self.verbose:
                        print(f"Received output line:\n{line}\n---")

                    line = self.line_postprocessor(line)

                    if line is None:
                        continue  # `line = None` is the postprocessor's signal to discard completely

                    if self.detect_active_line(line):
                        active_line = self.detect_active_line(line)
                        self.output_queue.put(
                            {
                                "type": "console",
                                "format": "active_line",
                                "content": active_line,
                            }
                        )
                        # Sometimes there's a little extra on the same line, so be sure to send that out
                        line = re.sub(r"##active_line\d+##", "", line)
                        if line:
                            self.output_queue.put(
                                {"type": "console", "format": "output", "content": line}
                            )
                    elif self.detect_end_of_execution(line):
                        # Sometimes there's a little extra on the same line, so be sure to send that out
                        line = line.replace("##end_of_execution##", "").strip()
                        if line:
                            self.output_queue.put(
                                {"type": "console", "format": "output", "content": line}
                            )
                        self.done.set()
                        break  # End of execution detected
                    elif is_error_stream and "KeyboardInterrupt" in line:
                        self.output_queue.put(
                            {
                                "type": "console",
                                "format": "output",
                                "content": "KeyboardInterrupt",
                            }
                        )
                        time.sleep(0.1)
                        self.done.set()
                        break
                    elif is_error_stream and re.search(
                        r"syntax error|unexpected end of file|illegal option|command not found",
                        line,
                        re.IGNORECASE,
                    ):
                        self.output_queue.put(
                            {
                                "type": "console",
                                "format": "output",
                                "content": "[ERROR] Command syntax or execution failure detected; stopping current command execution.",
                            }
                        )
                        self.done.set()
                        break
                    else:
                        self.output_queue.put(
                            {"type": "console", "format": "output", "content": line}
                        )

                except (OSError, ValueError) as e:
                    # Stream closed or other I/O error
                    if self.verbose:
                        print(f"Stream error: {e}")
                    break

        except Exception as e:
            if self.verbose:
                print(f"Error in handle_stream_output: {e}")
        finally:
            # Ensure we don't leave the thread hanging
            pass
