import smtplib
from email.message import EmailMessage
from queue import Queue, Empty
from threading import Thread
from typing import Any

from event_engine import EventEngine
from trader_engine_base import BaseEngine
from trader_setting import SETTINGS


class EmailEngine(BaseEngine):
    """
    Provides email sending function
    """

    def __init__(self, main_engine: Any, event_engine: EventEngine):
        super(EmailEngine, self).__init__(main_engine=main_engine, event_engine=event_engine, engine_name="email")

        self.thread: Thread = Thread(target=self.run)
        self.queue: Queue = Queue()
        self.active: bool = False

        self.main_engine.send_email = self.send_email

    def send_email(self, subject: str, content: str, receiver: str = "") -> None:
        # start email engine when sending it first time
        if not self.active:
            self.start()

        # use default receiver if not specified
        if not receiver:
            receiver = SETTINGS["email.receiver"]

        msg = EmailMessage()
        msg["From"] = SETTINGS["email.sender"]
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content(content)

        self.queue.put(msg)

    def run(self) -> None:
        while self.active:
            try:
                msg = self.queue.get(block=True, timeout=1)

                with smtplib.SMTP_SSL(
                        SETTINGS['email.server'], SETTINGS['email.port']
                ) as smtp:
                    smtp.login(
                        SETTINGS["email.username"], SETTINGS["email.password"]
                    )
                    print("login in okay")
                    print(msg)
                    smtp.send_message(msg)
            except Empty:
                pass

    def start(self) -> None:
        self.active = True
        self.thread.start()

    def close(self) -> None:
        if not self.active:
            return
        self.active = False
        self.thread.join()
