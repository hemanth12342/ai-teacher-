import os
import gspread
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.credentials_path = "credentials.json"
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        self.client = None
        self._init_client()

    def _init_client(self):
        # Refresh env var just in case
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", self.sheet_id)
        if not self.sheet_id:
            logger.warning("GOOGLE_SHEET_ID not set in environment.")
            return
            
        if not os.path.exists(self.credentials_path):
            logger.warning(f"{self.credentials_path} not found. Cannot authenticate to Google Sheets.")
            return
            
        try:
            self.client = gspread.service_account(filename=self.credentials_path)
            logger.info("Successfully connected to Google Sheets API.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")

    def export_attendance(self, room_id: str, records: list):
        # We re-init in case credentials were just added dynamically
        if not self.client:
            self._init_client()

        if not self.client:
            raise Exception("Google Sheets is not configured. Please ensure credentials.json exists and GOOGLE_SHEET_ID is set in the environment.")
            
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            try:
                worksheet = sheet.worksheet(room_id)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = sheet.add_worksheet(title=room_id, rows="100", cols="10")
                worksheet.append_row(["Username", "Role", "Joined At", "Left At", "Duration (Seconds)"])
            
            rows_to_append = []
            for r in records:
                if isinstance(r, dict):
                    rec = r
                else:
                    rec = r.model_dump()
                joined = str(rec.get("joined_at", ""))
                left = str(rec.get("left_at", ""))
                dur = rec.get("duration_seconds", 0)
                
                rows_to_append.append([
                    rec.get("username", "Unknown"),
                    rec.get("role", "student"),
                    joined,
                    left,
                    dur
                ])
                
            if rows_to_append:
                worksheet.append_rows(rows_to_append)
                
            return {"status": "success", "rows_added": len(rows_to_append)}
            
        except Exception as e:
            logger.error(f"Error exporting attendance to sheets: {e}")
            raise Exception(f"Failed to export to Google Sheets: {str(e)}")

google_sheets_service = GoogleSheetsService()
