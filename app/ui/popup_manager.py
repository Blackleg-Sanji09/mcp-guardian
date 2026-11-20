import asyncio
import threading
import queue
import tkinter as tk
import sys

from app.ui.approval_popup import show_approval_popup


class PopupManager:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.request_queue = queue.Queue()

        self.active_popups = 0
        self.popup_offset = 40

        # Tracks active popup windows by request ID.
        self.popup_windows = {}

        self.gui_thread = threading.Thread(
            target=self._run_gui,
            daemon=True,
        )

        self.gui_thread.start()

    def show_popup(
        self,
        request_id: str,
        tool_name: str,
        arguments: dict,
        approval_manager,
    ):
        self.request_queue.put(
            (
                request_id,
                tool_name,
                arguments,
                approval_manager,
            )
        )

    def _run_gui(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()

            self.root.after(100, self._process_queue)
            self.root.mainloop()

        except Exception as error:
            print(
                f"MCP Guardian GUI error: {error}",
                file=sys.stderr,
            )

    def _get_popup_position(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = 480
        window_height = 500

        offset = max(0, self.active_popups - 1) * self.popup_offset

        x = (screen_width - window_width) // 2 + offset
        y = (screen_height - window_height) // 2 + offset

        x = min(max(x, 0), screen_width - window_width)
        y = min(max(y, 0), screen_height - window_height)

        return x, y

    def _block_request_safely(
        self,
        request_id,
        approval_manager,
        reason,
    ):
        def block():
            try:
                approval_manager.block_request(
                    request_id,
                    reason,
                )
            except ValueError:
                # Request may already have timed out or been cleaned up.
                pass

        try:
            self.loop.call_soon_threadsafe(block)

        except RuntimeError:
            print(
                "Could not notify approval manager: event loop closed.",
                file=sys.stderr,
            )

    def _close_popup(self, request_id):
        """Close a popup safely from the Tk GUI thread."""
        popup = self.popup_windows.get(request_id)

        if popup is not None:
            try:
                popup.destroy()
            except tk.TclError:
                pass

            self.popup_windows.pop(request_id, None)

    def _process_queue(self):
        while True:
            try:
                (
                    request_id,
                    tool_name,
                    arguments,
                    approval_manager,
                ) = self.request_queue.get_nowait()

            except queue.Empty:
                break

            self.active_popups += 1
            position = self._get_popup_position()

            # Tracks whether this popup has already been resolved.
            decision_made = threading.Event()

            def handle_decision(
                decision,
                request_id=request_id,
                approval_manager=approval_manager,
                decision_made=decision_made,
            ):
                # Ignore late clicks or duplicate decisions.
                if decision_made.is_set():
                    return

                decision_made.set()

                def process_decision():
                    try:
                        if decision == "approved":
                            approval_manager.approve_request(request_id)
                        else:
                            approval_manager.block_request(
                                request_id,
                                "Blocked by user through MCP Guardian.",
                            )

                    except ValueError:
                        # Request is no longer pending.
                        pass

                try:
                    self.loop.call_soon_threadsafe(process_decision)

                except RuntimeError:
                    print(
                        "Could not process popup decision: "
                        "event loop closed.",
                        file=sys.stderr,
                    )

                # Clean up the popup reference and active count
                # on the Tk GUI thread.
                try:
                    self.root.after(
                        0,
                        lambda: self._finish_popup(
                            request_id,
                        ),
                    )
                except tk.TclError:
                    pass

            try:
                popup = show_approval_popup(
                    parent=self.root,
                    tool_name=tool_name,
                    arguments=arguments,
                    on_decision=handle_decision,
                    position=position,
                )

                self.popup_windows[request_id] = popup

                # Register timeout handling.
                def timeout_callback(
                    request_id=request_id,
                    decision_made=decision_made,
                ):
                    def close_on_gui_thread():
                        if not decision_made.is_set():
                            decision_made.set()

                            self._finish_popup(
                                request_id,
                            )

                    try:
                        self.root.after(
                            0,
                            close_on_gui_thread,
                        )
                    except tk.TclError:
                        pass

                approval_manager.register_timeout_callback(
                    request_id,
                    timeout_callback,
                )

            except Exception as error:
                print(
                    f"Failed to display approval popup: {error}",
                    file=sys.stderr,
                )

                self.active_popups = max(
                    0,
                    self.active_popups - 1,
                )

                self._block_request_safely(
                    request_id,
                    approval_manager,
                    "Approval popup failed to display. "
                    "Request blocked for safety.",
                )

        self.root.after(100, self._process_queue)

    def _finish_popup(self, request_id):
        """Clean up popup bookkeeping on the GUI thread."""
        self._close_popup(request_id)

        self.active_popups = max(
            0,
            self.active_popups - 1,
        )