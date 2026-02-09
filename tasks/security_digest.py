"""
Daily security digest generator
Uploads summary to Google Drive security_logs folder
"""
import asyncio
import logging
from datetime import datetime, timedelta
from backend.security.ip_monitor import aegis_monitor
from utils.drive_auth import get_drive_service, find_citadel_folder, get_or_create_subfolder, upload_json_to_drive

logger = logging.getLogger(__name__)

async def daily_security_digest():
    """
    Generate and upload daily security summary to Drive.
    Runs every 24 hours at midnight UTC.
    """
    while True:
        try:
            # Calculate seconds until next midnight UTC
            now = datetime.utcnow()
            next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_midnight = next_midnight + timedelta(days=1)
            seconds_until_midnight = (next_midnight - now).total_seconds()
            
            # Wait until midnight
            await asyncio.sleep(seconds_until_midnight)
            
            # Generate summary
            summary = aegis_monitor.get_daily_summary()
            
            logger.info(
                f"📊 DAILY SECURITY DIGEST: "
                f"{summary['total_events']} events, "
                f"{summary['auto_bans']} bans, "
                f"{summary['currently_banned']} IPs currently banned"
            )
            
            # Upload to Drive
            try:
                service = get_drive_service()
                folder_id = find_citadel_folder(service)
                
                # Get or create security_logs subfolder
                security_folder_id = get_or_create_subfolder(service, folder_id, 'security_logs')
                
                # Upload summary
                filename = f"security_digest_{summary['date']}.json"
                upload_json_to_drive(service, security_folder_id, filename, summary)
                
                logger.info(f"✅ Security digest uploaded to Drive: {filename}")
                
            except Exception as e:
                logger.error(f"Failed to upload security digest: {e}")
            
            # Clean up old events
            aegis_monitor.clear_old_events(days_to_keep=7)
            
        except Exception as e:
            logger.error(f"Error in daily security digest: {e}")
            await asyncio.sleep(3600)  # Retry in 1 hour on error
