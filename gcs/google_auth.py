import os

import gspread

def gspread_auth():
    filepath = os.getcwd() + "/gcs/gcs_client_secrets.json"
    gc = gspread.auth.oauth(credentials_filename=filepath)
    return gc

if __name__ == "__main__":
    gc = gspread_auth()
    spreadsheet = gc.open_by_key("1IAOJ1F38sSNVRHJH_c_BpwSbI3MLVu-yAaI2bV8jr7U")
    worksheet = spreadsheet.get_worksheet(0)
    worksheet.update_cell(1,1,"hello world")