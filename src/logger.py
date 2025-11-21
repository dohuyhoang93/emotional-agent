# src/logger.py

import sys

LOG_LEVELS = {
    "silent": 0,
    "info": 1,
    "verbose": 2
}

def log(context, message_level: str, message: str):
    """
    Logs a message if its level is greater than or equal to the context's log_level.

    Args:
        context: The current context object (e.g., AgentContext, OrchestrationContext)
                 which must have a 'log_level' attribute.
        message_level: The level of the message to be logged ('silent', 'info', 'verbose').
                       Messages with a higher numerical value (e.g., 'verbose') are
                       more detailed.
        message: The string message to log.
    """
    context_log_level_str = getattr(context, 'log_level', 'info') # Default to 'info' if not set
    context_log_level_value = LOG_LEVELS.get(context_log_level_str, LOG_LEVELS["info"])
    message_log_level_value = LOG_LEVELS.get(message_level, LOG_LEVELS["info"])

    if message_log_level_value <= context_log_level_value:
        print(message)

def log_error(context, message: str):
    """
    Logs an error message. Errors are always logged to stderr.
    """
    # Errors should always be printed. If log_level is 'silent', still log to stderr.
    print(f"ERROR: {message}", file=sys.stderr)
