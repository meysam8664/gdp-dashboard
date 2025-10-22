# 🚀 Quick Start Guide

## نحوه استفاده سریع | Quick Start

### نصب و اجرا | Installation & Running

#### 1. نصب وابستگی‌ها | Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. اجرای برنامه | Run Application
```bash
streamlit run streamlit_app.py
```

برنامه روی آدرس زیر اجرا می‌شود:
Application will run at: **http://localhost:8501**

### راهنمای سریع استفاده | Quick Usage Guide

#### صفحه اصلی | Main Interface

1. **دکمه اسکن | Scan Button**: برای جستجوی فوری فرصت‌های آربیتراژ
   - Click "🔍 Scan Now" to search for arbitrage opportunities

2. **تنظیمات کناری | Sidebar Settings**:
   - حداقل سود: 0-10% | Min Profit: 0-10%
   - اسکن خودکار | Auto-Scan: Enable/Disable
   - دارایی‌های مورد نظر | Assets: Select trading pairs

3. **فیلتر نتایج | Filter Results**:
   - نوع آربیتراژ | Type: Spatial, Triangular
   - سطح ریسک | Risk: LOW, MEDIUM, HIGH
   - حداقل سود | Min Profit %

#### تب‌های مختلف | Tabs

##### 📋 فرصت‌ها | Opportunities
- مشاهده تمام فرصت‌های شناسایی شده
- جزئیات کامل هر فرصت
- اطلاعات قیمت خرید و فروش

##### 📊 آنالیز | Analytics
- نمودار توزیع سود
- نمودار نوع فرصت‌ها
- تحلیل ریسک و سود

##### 🏥 سلامت صرافی‌ها | Exchange Health
- وضعیت زنده صرافی‌ها
- نرخ موفقیت اتصالات
- شمارش خطاها

### مثال استفاده | Usage Example

#### مرحله 1: تنظیمات اولیه | Step 1: Initial Setup
```
1. باز کردن برنامه | Open application
2. انتخاب دارایی‌ها از سایدبار | Select assets from sidebar
3. تنظیم حداقل سود به 1% | Set min profit to 1%
```

#### مرحله 2: اسکن بازار | Step 2: Scan Market
```
1. کلیک روی "Scan Now" | Click "Scan Now"
2. منتظر بمانید (2-5 ثانیه) | Wait (2-5 seconds)
3. مشاهده نتایج | View results
```

#### مرحله 3: تحلیل فرصت‌ها | Step 3: Analyze Opportunities
```
1. مرتب‌سازی بر اساس سود | Sort by profit
2. بررسی ریسک هر فرصت | Check risk level
3. مطالعه جزئیات مسیر معامله | Review trading path
```

### ویژگی‌های کلیدی | Key Features

#### 🔍 انواع آربیتراژ | Arbitrage Types

**1. Spatial Arbitrage (آربیتراژ مکانی)**
- تفاوت قیمت یک دارایی در صرافی‌های مختلف
- مثال: BTC در Binance ارزان‌تر از Coinbase

**2. Triangular Arbitrage (آربیتراژ مثلثی)**
- معاملات سه‌گانه در یک صرافی
- مثال: USDT → BTC → ETH → USDT

#### 🛡️ ارزیابی ریسک | Risk Assessment

- **🟢 LOW**: ایمن - صرافی‌های معتبر
- **🟡 MEDIUM**: متوسط - نیاز به دقت
- **🔴 HIGH**: پرخطر - احتیاط زیاد

#### 💰 محاسبه سود | Profit Calculation

برنامه به صورت خودکار محاسبه می‌کند:
The app automatically calculates:
- سود درصدی | Profit percentage
- سود مطلق | Absolute profit
- کارمزدها | Fees
- سرمایه مورد نیاز | Required capital

### تست سیستم | System Test

برای تست عملکرد سیستم:
To test system functionality:

```bash
python3 test_system.py
```

این دستور تست می‌کند:
This command tests:
- اتصال به صرافی‌ها | Exchange connectivity
- شناسایی فرصت‌ها | Opportunity detection
- مدیریت خطا | Error handling
- وضعیت سلامت | Health monitoring

### تنظیمات پیشرفته | Advanced Settings

#### فایل .env
کپی کردن و ویرایش:
Copy and edit:

```bash
cp .env.example .env
nano .env
```

تنظیمات قابل تغییر:
Configurable settings:
- `MIN_PROFIT_PCT`: حداقل سود
- `SCAN_INTERVAL`: فاصله اسکن
- `MAX_RETRIES`: تعداد تلاش مجدد
- `RATE_LIMIT_PER_SECOND`: محدودیت درخواست

### نکات مهم | Important Tips

#### ✅ بهترین شیوه‌ها | Best Practices

1. **شروع با سود پایین**
   - Start with low profit threshold (0.5-1%)

2. **بررسی ریسک**
   - Always check risk level before trading

3. **تایید دستی**
   - Manually verify opportunities before executing

4. **مدیریت سرمایه**
   - Only use capital you can afford to lose

5. **نظارت مداوم**
   - Monitor exchange health status

#### ⚠️ هشدارها | Warnings

- ⏱️ **زمان**: فرصت‌ها سریع از بین می‌روند
  - Opportunities disappear quickly
  
- 💸 **کارمزد**: همیشه کارمزدها را در نظر بگیرید
  - Always account for fees
  
- 🔒 **امنیت**: هرگز کلیدهای API را به اشتراک نگذارید
  - Never share API keys
  
- 📊 **تحقیق**: قبل از معامله تحقیق کنید
  - Research before trading

### رفع مشکلات | Troubleshooting

#### مشکل: برنامه اجرا نمی‌شود
#### Problem: App won't start

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### مشکل: فرصتی پیدا نمی‌شود
#### Problem: No opportunities found

- حداقل سود را کاهش دهید | Lower min profit threshold
- دارایی‌های بیشتری انتخاب کنید | Select more assets
- چند بار اسکن کنید | Scan multiple times

#### مشکل: خطای اتصال
#### Problem: Connection errors

- اینترنت خود را بررسی کنید | Check internet connection
- منتظر چند ثانیه بمانید | Wait a few seconds
- برنامه خودکار دوباره تلاش می‌کند | App auto-retries

### منابع بیشتر | More Resources

- 📖 مستندات کامل: README.md
- 🧪 تست سیستم: test_system.py
- ⚙️ تنظیمات: config.py
- 📝 لاگ‌ها: logs/ directory

### پشتیبانی | Support

برای سوالات و مشکلات:
For questions and issues:

1. بررسی README.md | Check README.md
2. اجرای test_system.py | Run test_system.py
3. بررسی لاگ‌ها | Check logs
4. گزارش مشکل در GitHub | Report issue on GitHub

---

**موفق باشید! | Good Luck!** 🚀💰

*یادآوری: معامله ریسک دارد. همیشه احتیاط کنید.*
*Reminder: Trading involves risk. Always be cautious.*
