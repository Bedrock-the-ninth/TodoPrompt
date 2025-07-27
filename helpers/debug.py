from importlib import import_module

getattr(import_module("send_reminder_message"), "send_reminder_runner")