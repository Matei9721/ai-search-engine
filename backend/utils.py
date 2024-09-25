import random


def generate_new_conversation_thread_id(existing_numbers, lower_bound=1, upper_bound=100):
    """
    Generate new thread id which does exist already
    :param existing_numbers: The thread ids that exist already for this user
    :param lower_bound: Lower bound for the conversation IDs
    :param upper_bound: Upper bound for the conversation IDs
    :return: New thread ID
    """
    while True:
        # Generate a random number
        new_chat_thread_id = random.randint(lower_bound, upper_bound)

        # Check if the new number is not in the existing list
        if new_chat_thread_id not in existing_numbers:
            return new_chat_thread_id
