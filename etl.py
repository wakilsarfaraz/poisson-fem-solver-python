import pyodbc
import pandas as pd
import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("etl_pipeline.log"),
                        logging.StreamHandler()
                    ])

# Function to clear the contents of a folder
def clear_folder(folder_path):
    logging.info(f"Starting to clear the contents of folder: {folder_path}")
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        logging.info(f"Contents of folder {folder_path} have been cleared.")
    except Exception as e:
        logging.error(f"Error while clearing folder {folder_path}: {e}")

# Function to create tables in the database
def manage_tables(connection_string):
    logging.info("Starting to manage tables in the database.")
    try:
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        # Paths to the SQL files
        drop_payment_table_file = os.path.join('queries', 'drop_payment_summary_table.sql')
        drop_duration_table_file = os.path.join('queries', 'drop_duration_summary_table.sql')
        create_payment_table_file = os.path.join('queries', 'create_payment_summary_table.sql')
        create_duration_table_file = os.path.join('queries', 'create_duration_summary_table.sql')

        # Helper function to execute SQL files
        def execute_sql_file(file_path):
            with open(file_path, 'r') as file:
                sql = file.read()
                cursor.execute(sql)

        # Execute drop table SQL files
        execute_sql_file(drop_payment_table_file)
        execute_sql_file(drop_duration_table_file)
        connection.commit()

        # Execute create table SQL files
        execute_sql_file(create_payment_table_file)
        execute_sql_file(create_duration_table_file)
        connection.commit()

        logging.info("Tables payment_summary_table and duration_summary_table have been recreated in the database.")
    except pyodbc.Error as e:
        logging.error(f"Error managing tables: {e}")
    except FileNotFoundError as e:
        logging.error(f"SQL file not found: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()

# Function to retrieve payments summary using an SQL file
def calculate_payments(sql_file_path, connection_string):
    logging.info("Starting to calculate payments summary.")
    try:
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        with open(sql_file_path, 'r') as file:
            sql_query = file.read()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        payments_summary = pd.DataFrame((tuple(t) for t in rows)) 
        payments_summary.columns = ['Records', 'Minimum', 'Maximum', 'Total', 'Average']
        logging.info("Payments summary successfully retrieved.")
    except pyodbc.Error as e:
        logging.error(f"Error executing payments query: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()
    return payments_summary

# Function to retrieve duration summary from an SQL query
def calculate_duration(sql_file_path, connection_string):
    logging.info("Starting to calculate duration summary.")
    try:
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        with open(sql_file_path, 'r') as file:
            sql_query = file.read()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        duration_summary = pd.DataFrame((tuple(t) for t in rows)) 
        duration_summary.columns = ['Minimum', 'Maximum', 'Total', 'Average']
        logging.info("Duration summary successfully retrieved.")
    except pyodbc.Error as e:
        logging.error(f"Error executing duration query: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()
    return duration_summary

# Function to write a DataFrame back into the database
def write_dataframe_to_db(dataframe, table_name, connection_string):
    logging.info(f"Starting to write DataFrame to table: {table_name}")
    try:
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()
        # Insert rows into the database
        for index, row in dataframe.iterrows():
            placeholders = ', '.join(['?'] * len(row))
            columns = ', '.join(dataframe.columns)
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(row))
        connection.commit()
        logging.info(f"Data successfully written to table: {table_name}.")
    except pyodbc.Error as e:
        logging.error(f"Error writing to database table {table_name}: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()

# Function to write DataFrame to a text file
def write_local_txt_output(dataframe, folder_path, file_name):
    logging.info(f"Starting to write DataFrame to text file: {file_name}")
    try:
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, file_name)
        dataframe.to_csv(file_path, sep='\t', index=False)
        logging.info(f"Processed data successfully written to {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"An error occurred while writing to text file {file_name}: {e}")
        return None

# Run the pipeline
if __name__ == "__main__":
    connection_string = '''Driver={ODBC Driver 18 for SQL Server};
                            Server=tcp:sakilam25fr5nged25q.database.windows.net,1433;
                            Database=sakila;Uid=corndeladmin;Pwd={Password01};
                            Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'''
    target_folder = "reports"

    clear_folder(target_folder)
    manage_tables(connection_string)
    payments_df = calculate_payments("queries/payments.sql", connection_string)
    duration_df = calculate_duration("queries/filmduration.sql", connection_string)

    write_dataframe_to_db(payments_df, "payment_summary_table", connection_string)
    write_dataframe_to_db(duration_df, "duration_summary_table", connection_string)

    write_local_txt_output(payments_df, "reports", "payment_summary.txt")
    write_local_txt_output(duration_df, "reports", "duration_summary.txt")
