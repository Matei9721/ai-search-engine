from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import json

"""
This class encapsulates all the logic for communicating with the SQLite database that stores all the chat history and
enables the graph to create the illusion of a conversation.
"""


# TODO: Add type casting

class ChatDatabase:
    def __init__(self, database_location: str = "database/checkpoints.sqlite"):
        self.database_location = database_location
        try:
            self.memory = SqliteSaver.from_conn_string(database_location)
        except Exception as _:
            raise Exception("Could not load database from specified path")

    def get_graph_connection(self):
        """
        Returns a SQLiteSaver object to be used by the graph
        :return: SqliteSaver
        """
        try:
            return SqliteSaver.from_conn_string(self.database_location)
        except Exception as _:
            raise Exception("Could not load database from specified path")

    def get_checkpoint_by_thread_id(self, thread_id):
        """
        Returns a checkpoint for a specific thread id
        :param thread_id: The thread id we want to retrieve the conversation from
        :return: Checkpoint
        """
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(self.database_location)
            cursor = conn.cursor()
        except Exception as _:
            raise Exception("Could not establish connection to the database!")

        try:
            # SQL query to fetch data by thread_id
            query = "SELECT * FROM checkpoints WHERE thread_id = ?"

            # Execute the query with the thread_id parameter
            cursor.execute(query, (thread_id,))

            # Fetch the result
            result = cursor.fetchall()  # Use fetchall() to get multiple rows
        except Exception as _:
            # raise Exception("Failed to retrieve SQL statement from database!")
            print("Failed to retrieve SQL statement from database!")
            return None

        # Close the database connection
        conn.close()

        return result

    def get_checkpoints_by_user_id(self, thread_id_prefix):
        """
        Get all checkpoints of a user
        :param thread_id_prefix: The prefix / unique user id
        :return: All checkpoints for that user
        """
        # Connect to the SQLite database
        conn = sqlite3.connect(self.database_location)
        cursor = conn.cursor()

        # SQL query to fetch data where id starts with thread_id_prefix and parent_ts is NULL
        query = "SELECT * FROM checkpoints WHERE thread_id LIKE ? AND parent_ts IS NULL"

        # Execute the query with the thread_id_prefix parameter followed by a wildcard
        cursor.execute(query, (thread_id_prefix + '%',))  # Add '%' for wildcard match

        # Fetch the result
        result = cursor.fetchall()

        # Close the database connection
        conn.close()

        return result

    def reset_database_state(self):
        """
        Delete all the data in the SQLite tables
        :return: None
        """
        # Connect to the SQLite database
        conn = sqlite3.connect(self.database_location)
        cursor = conn.cursor()

        # Query to find all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Loop over all tables and delete their data
        for table_name in tables:
            table_name = table_name[0]
            cursor.execute(f"DELETE FROM {table_name};")
            print(f"Cleared table: {table_name}")

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

    def chat_history_from_checkpoint(self, user_identifier: str, thread: int):
        """
        Process the checkpoint data into Streamlit compatible chat history
        :param user_identifier: User unique identifier
        :param thread: Conversation ID
        :return:
        """
        streamlit_conversation = [{"role": "assistant",
                                   "content": "Hello, I am a bot that can search the web. How can I help you?"}]
        try:
            last_checkpoint = self.get_checkpoint_by_thread_id(thread_id=user_identifier + str(thread))
            last_conversation = json.loads(last_checkpoint[-1][3].decode("utf-8"))["channel_values"]["messages"]
            for message in last_conversation:
                if message['kwargs']["type"] == "human":
                    # print(f"Human: {message['kwargs']['content']}")
                    streamlit_conversation.append({"role": "user", "content": message['kwargs']['content']})
                elif message['kwargs']["type"] == "ai":
                    # print(f"AI: {message['kwargs']['content']}")
                    streamlit_conversation.append({"role": "assistant", "content": message['kwargs']['content']})
        except Exception as e:
            print("Failed to load conversation or no conversation to load.")

        return streamlit_conversation

    def get_all_chats_history_for_user(self, user_id: str):
        """
        Format all the checkpoints in a Streamlit friendly way to display all chat histories for an user
        :param user_id: User unique ID
        :return: User's chat history
        """
        user_history = {"chat_id": [], "chat_start": [], "chat_timestamp": []}
        try:
            # Get all checkpoints for this user id
            user_checkpoints = self.get_checkpoints_by_user_id(user_id)
            for checkpoint in user_checkpoints:
                checkpoint_data = json.loads(checkpoint[3].decode("utf-8"))
                user_history["chat_timestamp"].append(checkpoint_data["ts"])
                user_history["chat_id"].append(int(checkpoint[0].split(user_id)[1]))
                user_history["chat_start"].append(
                    checkpoint_data["channel_values"]["__start__"]["messages"][0]["kwargs"]["content"])

        except Exception as e:
            print("Failed to load conversation or no conversation to load.")

        return user_history
