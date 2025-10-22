"""
Multi-channel notification system
Supports Telegram, Email, Discord, and Webhooks
"""

import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Optional dependency
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not installed. Web notifications (Telegram, Discord, Webhook) unavailable. Install with: pip install aiohttp")


@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    
    # Telegram
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # Email
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_from: str = ""
    email_password: str = ""
    email_to: List[str] = None
    
    # Discord
    discord_enabled: bool = False
    discord_webhook_url: str = ""
    
    # Custom Webhook
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_headers: Dict = None
    
    # General settings
    min_profit_for_notification: float = 2.0
    notification_cooldown: int = 60  # seconds
    
    def __post_init__(self):
        if self.email_to is None:
            self.email_to = []
        if self.webhook_headers is None:
            self.webhook_headers = {}


class NotificationManager:
    """Manage notifications across multiple channels"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.last_notification_time = {}
        self.notification_count = 0
    
    async def send_opportunity_alert(self, opportunity) -> bool:
        """
        Send alert for high-profit opportunity
        
        Args:
            opportunity: ArbitrageOpportunity object
            
        Returns:
            True if sent successfully
        """
        # Check if opportunity meets threshold
        if opportunity.profit_percentage < self.config.min_profit_for_notification:
            return False
        
        # Check cooldown
        key = f"{opportunity.arbitrage_type.value}_{opportunity.asset}"
        if key in self.last_notification_time:
            elapsed = (datetime.now() - self.last_notification_time[key]).seconds
            if elapsed < self.config.notification_cooldown:
                logger.debug(f"Notification cooldown active for {key}")
                return False
        
        # Prepare message
        message = self._format_opportunity_message(opportunity)
        
        # Send to all enabled channels
        results = []
        
        if self.config.telegram_enabled:
            results.append(await self._send_telegram(message))
        
        if self.config.email_enabled:
            results.append(await self._send_email(
                "🚨 Arbitrage Alert - High Profit Opportunity!",
                message
            ))
        
        if self.config.discord_enabled:
            results.append(await self._send_discord(message))
        
        if self.config.webhook_enabled:
            results.append(await self._send_webhook({
                'type': 'arbitrage_opportunity',
                'opportunity': self._opportunity_to_dict(opportunity),
                'message': message,
                'timestamp': datetime.now().isoformat()
            }))
        
        # Update last notification time
        if any(results):
            self.last_notification_time[key] = datetime.now()
            self.notification_count += 1
            logger.info(f"Sent alert for {opportunity.asset} - {opportunity.profit_percentage:.2f}%")
        
        return any(results)
    
    def _format_opportunity_message(self, opportunity) -> str:
        """Format opportunity as readable message"""
        return f"""
🚨 **ARBITRAGE OPPORTUNITY DETECTED!** 🚨

💰 **Profit**: {opportunity.profit_percentage:.2f}% (${opportunity.profit_absolute:.2f})
📊 **Type**: {opportunity.arbitrage_type.value.upper()}
💎 **Asset**: {opportunity.asset}
📍 **Path**: {' → '.join(opportunity.path)}

💵 **Buy Price**: ${opportunity.buy_price:.4f}
💵 **Sell Price**: ${opportunity.sell_price:.4f}

🛡️ **Risk**: {opportunity.risk_level}
🎯 **Confidence**: {opportunity.confidence*100:.0f}%
💰 **Required Capital**: ${opportunity.required_capital:.2f}
💸 **Estimated Fees**: ${opportunity.fees_estimated:.4f}

⏰ **Time**: {opportunity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

⚡ **Act quickly - arbitrage opportunities disappear fast!**
        """.strip()
    
    def _opportunity_to_dict(self, opportunity) -> Dict:
        """Convert opportunity to dictionary"""
        return {
            'id': opportunity.opportunity_id,
            'type': opportunity.arbitrage_type.value,
            'asset': opportunity.asset,
            'profit_percentage': opportunity.profit_percentage,
            'profit_absolute': opportunity.profit_absolute,
            'buy_price': opportunity.buy_price,
            'sell_price': opportunity.sell_price,
            'source': opportunity.source,
            'destination': opportunity.destination,
            'path': opportunity.path,
            'confidence': opportunity.confidence,
            'risk_level': opportunity.risk_level,
            'required_capital': opportunity.required_capital,
            'timestamp': opportunity.timestamp.isoformat()
        }
    
    async def _send_telegram(self, message: str) -> bool:
        """Send message via Telegram"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not installed. Cannot send Telegram notifications.")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.config.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Telegram notification sent")
                        return True
                    else:
                        logger.error(f"Telegram error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False
    
    async def _send_email(self, subject: str, body: str) -> bool:
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_to)
            
            # Add body
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(self._format_html_email(body), 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_email_sync,
                msg
            )
            
            logger.info("Email notification sent")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _send_email_sync(self, msg):
        """Send email synchronously"""
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            server.starttls()
            server.login(self.config.email_from, self.config.email_password)
            server.send_message(msg)
    
    def _format_html_email(self, text: str) -> str:
        """Convert plain text to HTML email"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ background: #ff6b6b; color: white; padding: 20px; border-radius: 10px; }}
                .opportunity {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #2ecc71; }}
                .profit {{ font-size: 24px; color: #27ae60; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <pre>{text}</pre>
            </div>
        </body>
        </html>
        """
        return html
    
    async def _send_discord(self, message: str) -> bool:
        """Send message via Discord webhook"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not installed. Cannot send Discord notifications.")
            return False
            
        try:
            payload = {
                'content': message,
                'username': 'Arbitrage Bot',
                'avatar_url': 'https://cdn-icons-png.flaticon.com/512/2103/2103633.png'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.discord_webhook_url, 
                                       json=payload) as response:
                    if response.status in [200, 204]:
                        logger.info("Discord notification sent")
                        return True
                    else:
                        logger.error(f"Discord error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False
    
    async def _send_webhook(self, data: Dict) -> bool:
        """Send data to custom webhook"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not installed. Cannot send webhook notifications.")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    json=data,
                    headers=self.config.webhook_headers
                ) as response:
                    if response.status == 200:
                        logger.info("Webhook notification sent")
                        return True
                    else:
                        logger.error(f"Webhook error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False
    
    async def send_daily_summary(self, stats: Dict) -> bool:
        """Send daily summary report"""
        message = f"""
📊 **DAILY ARBITRAGE SUMMARY** 📊

📅 **Date**: {datetime.now().strftime('%Y-%m-%d')}

🎯 **Opportunities Found**: {stats.get('total_opportunities', 0)}
💰 **Average Profit**: {stats.get('avg_profit', 0):.2f}%
🚀 **Max Profit**: {stats.get('max_profit', 0):.2f}%
📉 **Min Profit**: {stats.get('min_profit', 0):.2f}%

📊 **By Type**:
{self._format_dict(stats.get('by_type', {}))}

🛡️ **By Risk**:
{self._format_dict(stats.get('by_risk', {}))}

🔔 **Notifications Sent**: {self.notification_count}
        """.strip()
        
        results = []
        
        if self.config.telegram_enabled:
            results.append(await self._send_telegram(message))
        
        if self.config.email_enabled:
            results.append(await self._send_email(
                "📊 Daily Arbitrage Summary",
                message
            ))
        
        return any(results)
    
    def _format_dict(self, d: Dict) -> str:
        """Format dictionary as readable text"""
        return '\n'.join(f"  - {k}: {v}" for k, v in d.items())
    
    async def test_notifications(self) -> Dict[str, bool]:
        """Test all notification channels"""
        results = {}
        
        test_message = "🧪 Test notification from Arbitrage Finder"
        
        if self.config.telegram_enabled:
            results['telegram'] = await self._send_telegram(test_message)
        
        if self.config.email_enabled:
            results['email'] = await self._send_email(
                "Test Notification",
                test_message
            )
        
        if self.config.discord_enabled:
            results['discord'] = await self._send_discord(test_message)
        
        if self.config.webhook_enabled:
            results['webhook'] = await self._send_webhook({
                'type': 'test',
                'message': test_message,
                'timestamp': datetime.now().isoformat()
            })
        
        return results
