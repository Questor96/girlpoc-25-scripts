import os

import gspread

def gspread_auth():
    filepath = os.getcwd() + "/gcs/gcs_service_account_secrets.json"
    gc = gspread.service_account(filepath)
    return gc

if __name__ == "__main__":
    gc = gspread_auth()
    print(gc.list_spreadsheet_files())