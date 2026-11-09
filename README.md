# ربات انتشار خودکار محتوای فوتبالی در کانال تلگرام

یک سیستم کامل، قطعی (deterministic) و **بدون سرور، بدون هزینه و بدون دانش عمیق فوتبال** که
چهار نوع پست به‌صورت خودکار در یک کانال تلگرام فارسی منتشر می‌کند:

| نوع پست | توضیح | زمان (به وقت تهران) |
|---|---|---|
| 📅 برنامه‌ی امروز | بازی‌های امروز لیگ‌های انتخابی، گروه‌بندی‌شده، با ساعت تهران | ساعت ۹ |
| ⚽ مرور نتایج | نتایج دیروز، بازی‌های پرگل‌تر اول | ساعت ۱۰ |
| 📊 کارت آماری روز | چرخشی بین جدول گلزنان / صدرنشینان جدول / هتریک‌های اخیر | ساعت ۱۴ |
| ⏰ یادآور بازی | حدوداً ۱۲ ساعت قبل از شروع هر بازی | هر ساعت |

هر پست یک **کارتِ تصویری برندشده** (۱۰۸۰×۱۳۵۰) و یک **کپشن فارسی** دارد.

---

## معماری

```
sources  →  facts  →  writer  →  cards  →  telegram
(داده خام) (واقعیت)   (متن)      (تصویر)   (انتشار)
```

هر لایه فقط با لایه‌ی بعدی حرف می‌زند. لایه‌ی `telegram` تنها جایی است که به تلگرام
وابسته است؛ اگر بعداً اینستاگرام/توییتر اضافه کنید، بقیه‌ی خط لوله تغییر نمی‌کند.

- `sources/` — football-data.org (v4)، thesportsdb.com (لیگ ایران)، Gemini (اختیاری)،
  داده‌ی نمونه (demo)، کش دیسکی با TTL
- `facts/` — تبدیل داده خام به بسته‌های واقعیت JSON با کلید `type`
  (`fixtures | recap | scorers | standings | hat_tricks | reminder`)
- `writer/` — قالب آماده فارسی (تکاملی قطعی) و مدل زبانی با **نگهبان اعداد**
- `cards/` — کارت با Pillow و فونت Vazirmatn، چیدمان‌هایgruppe‌بندی‌شده
- `telegram/` — Bot API (sendPhoto / sendMessage)، حافظه‌ی ضدتکرار

## نصب و راه‌اندازی (قدم‌به‌قدم)

### ۱. قبل از همه

```bash
python3 --version        # نیاز به Python 3.12+ (۳.۱۱ هم کار می‌کند)
git clone <repo-address>
cd telegram_bot_football
pip install -r requirements.txt
```

### ۲. ساخت ربات با BotFather

۱. در تلگرام، به `@BotFather` پیام دهید: `/newbot`
۲. یک نام و **username** برای ربات انتخاب کنید (مثلاً `MyChannelBot`)
۳. **توکن** ربات را کپی کنید — این دقیقاً یک توکن است:

### ۳. ادمین کردن ربات در کانال

۱. ربات را در کانال اضافه کنید (با Member role)
۲. username کانال را یادداشت کنید (مثلاً `my_football_channel`)

### ۴. گرفتن توکن رایگان football-data.org

1. روی [football-data.org](https://www.football-data.org/) ثبت‌نام کنید
2. در پنل، یک API Key كپى کنید (پلن رایگان: ۱۰ درخواست در دقیقه)
3. محدودیت‌های واقعی پلن رایگان را درجدول زیر ببینید

### ۵. کلید thesportsdb.com (لیگ ایران)

1. روی [thesportsdb.com](https://www.thesportsdb.com/) یک حساب بسازید و کلید بگیرید
2. ⚠️ **کلید تست عمومی `123` به‌شدت rate-limit می‌شود** و متن `error code: 1015`
   برمی‌گرداند (پاسخ JSON نیست). این حالت را تشخیص می‌دهد، retry کوتاه می‌زند و
   در نهایت با پیام واضح رد می‌شود — هرگز کرش نمی‌کند. اگر از این کلید استفاده می‌کنید،
   ممکن است لیگ ایران همیشه خالی باشد.

### ۶. کلید Gemini (اختیاری)

1. روی [aistudio.google.com](https://aistudio.google.com/) کلید API بسازید
2. پیش‌فرض مدل `gemini-2.5-flash` است
3. **اگر کلید نباشد، سیستم کامل کار می‌کند** — فقط از قالب آماده فارسی استفاده می‌کند

### ۷. تنظیم متغیرهای محیطی

کپی `.env.example` را به `.env` کنید و مقادیر را وارد کنید:

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHANNEL_ID=-1001234567890
FOOTBALL_DATA_TOKEN=your-football-data-token
THESPORTSDB_KEY=your-thesportsdb-key
GEMINI_API_KEY=your-gemini-key   # اختیاری
```

> هیچ کلیدی در کد یا فایل کامیت‌شده نیست. متغیرهای محیطی تنها راه خواندن کلیدها هستند.

### ۸. config.yaml

تنها فایلی که کاربر عادی دست می‌زند:

```yaml
channel:
  username: "my_football_channel"   # username کانال تلگرام
  brand: "برندِ کانال"              # نام برند روی کارت
  source_link: ""                   # لینک منبع (مثلاً سایت رسمی لیگ)
timezone: "Asia/Tehran"
competitions:                        # لیگ‌های اروپایی
  - {code: PL,  fa: "لیگ برتر انگلیس"}
  - {code: PD,  fa: "لالیگا"}
  - {code: SA,  fa: "سری آ"}
  - {code: BL1, fa: "بوندس‌لیگا"}
  - {code: CL,  fa: "لیگ قهرمانان اروپا"}
iran_league: {enabled: true, league_id: 4742, fa: "لیگ برتر خلیج فارس", season: "2026-2027"}
posts: {daily_digest_hour: 9, stat_card_hour: 14, recap_hour: 10, reminder_hours_before: 12}
theme: {bg_top: "#0B1B2B", bg_bottom: "#111C26", accent: "#00E08A", accent2: "#FFC247", text: "#FFFFFF", muted: "#93A4B5"}
model: {enabled: true, provider: "gemini", name: "gemini-2.5-flash", max_output_tokens: 400}
```

### ۹. تست لوکال (بدون هیچ کلیدی)

```bash
python run.py --job demo    # شش کارت PNG + شش فایل کپشن در samples/ + preview.html
python run.py --job test    # تست نگهبان اعداد، bidi، ارقام فارسی، چیدمان کارت‌ها
python run.py --job daily   # بدون کلید: کرش نمی‌کند، می‌گوید «داده در دسترس نیست»
```

### ۱۰. بردن روی گیت‌هاب و اجرای خودکار

1. کد را روی یک مخزن GitHub push کنید
2. Secrets اضافه کنید: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`,
   `FOOTBALL_DATA_TOKEN`, `THESPORTSDB_KEY`, `GEMINI_API_KEY` (اختیاری)
3. workfolow `.github/workflows/posts.yml` اجرا می‌شود:
   - **cron** `5 * * * *` (هر ساعت، UTC — به وقت تهران اختلاف دارد)
   - **workflow_dispatch** برای اجرای دستی با انتخاب job
   - **permissions: contents: write** — برای commit کردن state/
   - **concurrency** — جلوگیری از اجرای هم‌زمان
   - step آخر: state/ را کامیت و push می‌کند (این تنها راه بقای حافظه بین اجراها است)

> ⚠️ **هشدار مهم:** گیت‌هاب اکشنز بعد از **۶۰ روز بی‌کامی**، زمان‌بندی را خاموش می‌کند.
> برای زنده ماندن cron، باید حداقل یک execute شدن workflow در هر ۶۰ روز داشته باشید
> (مثلاً یک `workflow_dispatch` دستی، یا یک action دیگری که داخل مخزن فعال می‌شود).

### eleven. شخصی‌سازی

- **تبدیل رنگ:** `theme` در config.yaml
- **فونت:** Vazirmatn از `assets/fonts/` (Regular/Medium/Bold/Black)
- **لیگ‌ها:** `competitions` در config.yaml (code football-data.org)
- **ساعت پست‌ها:** `posts` در config.yaml
- **کپشن:** templates در `writer/templates.py` یا دسترسی مدل Gemini

## محدودیت‌های واقعی (جدول)

| سرویس | پلن | محدودیت واقعی | کاربرد |
|---|---|---|---|
| football-data.org | رایگان | ۱۰ درخواست/دقيقه، ۴ لیگ فعال (PL, PD, SA, BL1) + CL | لیگ‌های اروپایی |
| thesportsdb.com | رایگان | محدودیتdium، کلید `123` rate-limit شد (error 1015) | لیگ ایران |
| Gemini API | رایگان | محدودیت جمعیتی/روز (gemini-2.5-flash) | نوشتار کپشن (اختیاری) |
| Telegram Bot API | رایگان | ۳۰ پیام/ثانيه، ۱۰۲۴ کاراکتر کپشن sendPhoto | انتشار |

## عیب‌یابی (نخستين خطاها)

| پیام/خطا | دلیل | راه‌حل |
|---|---|---|
| `این endpoint در پلن رایگان نیست` | standings/scorers برای لیگ‌هایی که پلن رایگان ندارد | لیگ را از config حذف کنید |
| `error code: 1015` | thesportsdb rate-limit (کلید `123`) | کلید واقعی بخرید/بگیرید، منتظر بمانید |
| `داده در دسترس نیست` | کلید FOOTBALL_DATA_TOKEN/THESPORTSDB_KEY تنظیم نشده | .env یا Secrets را بررسی کنید |
| `this endpoint is not available in the free plan` | football-data | switch به پلن paid (پیش‌نمایش رایگان هم هست) |
| کپشن طولانی | sendPhoto حداکثر ۱۰۲۴ کاراکتر دارد | در telegram/api.py کوتاه می‌شود |
| متن فارسی خوانا نیست | Pillow بدون raqm | `pip install --force-reinstall Pillow` (pil با libraqm) |
| cron خاموش شد | ۶۰ روز بی‌کامی | یک workflow_dispatch دستی بفرستید |

## جدول کارتها

- **برنامه‌ی امروز:** لیست گروه‌بندی‌شده با ستون ساعت (بر اساس hour)
- **مرور نتایج:** لیست نتایج، بازی‌های پرگل‌تر اول
- **یادآور:** عدد بزرگ «۱۲ ساعت» وسط‌چین + دو تیم + ساعت
- **گلزنان/جدول/هتریک:** لیست رتبه‌دار با چیپ شماره و عدد بزرگ در راست

## نکات تکنیکی (تل‌های فنی)

1. **دوجهته‌شدن متن فارسی در Pillow:** اگر Pillow با libraqm کامپایل شده باشد
   (`PIL.features.check("raqm")`)، متن خام را با `direction="rtl"/"ltr"` و `language="fa"`
   بدهید. اگر raqm نبود، مسیر `arabic_reshaper + get_display` را بروید. هرگز هر دو را با هم
   استفاده نکنید (متن دوبار معکوس می‌شود). جهت را از محتوا تشخیص دهید.
2. **ترکیب آلفا:** کشیدن با رنگ RGBA روی تصویر RGBA جایگزین می‌شود، ترکیب نیست.
   راه حل: لایه‌ی جدا با `alpha_composite` نشانده کنید.
3. **نیم‌فاصله (ZWNJ):** با raqm درست کار می‌کند. متن را pre-process نکنید که ZWNJ را حذف کنید.
4. **ارقام فارسی:** در همه‌ی خروجی‌های متنی یکدست (هم کپشن، هم کارت).
5. **ساعت تهران:** هرگز از ساعت سیستم استفاده نکنید. `zoneinfo.ZoneInfo("Asia/Tehran")`
   و `jdatetime` برای تاریخ شمسی.
6. **برش روز:** یک «روز تهران» با یک روز UTC یکی نیست (تهران UTC+3:30). بازه‌ی روز را
   حساب کنید، حاشیه بگذارید، سپس فیلتر کنید که تاریخ تهران بازی با تاریخ هدف بخواند.
7. **sendPhoto:** کپشن حداکثر ۱۰۲۴ کاراکتر دارد؛ متن بلندتر خطا می‌دهد.
8. **گیت‌هاب اکشنز:** هرگز pip install بدون cache نکنید (actions/cache). اجرای ساعتی باید سبک بماند.

## نمونه‌ی اجرا

```bash
$ python run.py --job demo
=== بسته‌های واقعیت (demo، فقط JSON) ===
{"type": "fixtures", "date": "۱۴۰۵/۰۸/۱۸", "count": 5, "groups": [...]}
...
=== رندر کارت‌ها و کپشن‌ها ===
[demo] fixtures: samples/demo_fixtures.png + caption 329 کاراکتر
[demo] recap: samples/demo_recap.png + caption 254 کاراکتر
...
[demo] انجام شد.
```

پیش‌نمایش نهایی در `samples/preview.html` — شبیه چت تلگرام، تصاویر base64 درون‌خطی،
بدون هیچ منبع خارجی.
