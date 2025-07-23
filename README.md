# Uma Musume Club Member Fan Count Scraper

A simple Python script to scrape in‑game fan counts for Uma Musume Club members and optionally publish the results to Google Sheets and Discord.

---

## 🚀 Features

* **Real‑time scraping** of fan counts directly from the game window
* **CSV output** (`uma.csv`) for easy analysis
* **Optional integrations**:

  * Google Sheets (push updates to a spreadsheet)
  * Discord (send notifications via webhook)

---

## 🔧 Installation

1. **Clone this repo**:

   ```bash
   git clone https://github.com/yourusername/uma-scraper.git
   cd uma-scraper
   ```

2. **Install PyTorch** (required by OCR backends):

   ```bash
   # Visit https://pytorch.org/get-started/locally/ and choose the right command
   pip install torch torchvision torchaudio
   ```

3. **Install other dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Usage

1. **Launch the game** on your **primary** monitor.
2. Navigate in the game to: **Club** → **Club Menu** → **Club Info**.
3. Run the scraper:

   ```bash
   python umav2.py
   ```
4. **Alt+Tab** back to the game window while the script initializes.
5. When complete, results will be written to:

   ```text
   uma.csv
   ```

> ⚠️ Currently only supports a single monitor setup. Multi‑monitor support is coming soon!

---

## 📊 Google Sheets Integration *(Optional)*

Integrate with Google Sheets to automatically append or update rows in your spreadsheet.

1. **Create a Service Account**

   * Go to the [Google Cloud Console Service Accounts page](https://cloud.google.com/iam/docs/service-accounts-create).
   * Click **+ Create Service Account**, give it a name (e.g., `uma-scraper-sa`).
   * Grant it the **Editor** role (or just **Sheets API Editor**).
   * Finish and download the **JSON key** file.

2. **Enable the Google Sheets API**

   * In the Cloud Console, navigate to **APIs & Services** → **Library**.
   * Search for **Google Sheets API** and click **Enable**.

3. **Prepare your Spreadsheet**

   * Create a new sheet or open an existing one.
   * Copy the **Spreadsheet ID** from its URL:

     ```
     https://docs.google.com/spreadsheets/d/<SPREADSHEETID>/edit
     ```

* Share the sheet with your service account’s email (found in the JSON file, e.g., `uma-scraper-sa@….iam.gserviceaccount.com`) with **Editor** permission.


## 🔔 Discord Integration *(Optional)*

Send a notification to your Discord channel whenever the scrape runs.

1. **Create a Webhook**

   * Open your Discord server settings → **Integrations** → **Webhooks** → **New Webhook**.
   * Copy the **Webhook URL**.

2. **Add to `.env`**

   ```ini
   WEBHOOK=https://discord.com/api/webhooks/…
   ```



## 🗂 Project Structure

```
├── umav2.py          # Main scraper script
├── requirements.txt  # Dependency list
├── credentials.json  # Google service account key (gitignored)
├── .env              # Environment variables (gitignored)
└── uma.csv           # Output CSV file
```

---

