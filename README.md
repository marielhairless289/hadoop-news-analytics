# HW2 - News Category Dataset Analysis

## Project Log

This file documents every step taken in this project, including all commands and observations.

---

## Step 1: Dataset Download

**Source:** Kaggle — [News Category Dataset](https://www.kaggle.com/datasets/rmisra/news-category-dataset)

**File downloaded:** `News_Category_Dataset_v3.json`

- The dataset is from HuffPost and contains news articles.
- Each line in the file is a JSON object (newline-delimited JSON / NDJSON format).
- Fields in each record:
  - `link` — URL to the article
  - `headline` — Article headline
  - `category` — News category (e.g., U.S. NEWS, COMEDY, POLITICS, etc.)
  - `short_description` — Brief summary of the article
  - `authors` — Author name(s)
  - `date` — Publication date (format: YYYY-MM-DD)

---

## Step 2: Trim the Dataset

To avoid working with the full dataset, the first 5000 lines were extracted into a smaller file.

**Command:**
```bash
head -n 5000 News_Category_Dataset_v3.json > news_headlines.txt
```

**Result:** Created `news_headlines.txt` containing the first 5000 records from the original dataset.

---

## Step 3: Verify the Trimmed File

Checked the first 3 lines of the trimmed file to confirm correct format and content.

**Command:**
```bash
head -n 3 news_headlines.txt
```

**Output (sample records):**
```json
{"link": "https://www.huffpost.com/entry/covid-boosters-uptake-us_n_632d719ee4b087fae6feaac9", "headline": "Over 4 Million Americans Roll Up Sleeves For Omicron-Targeted COVID Boosters", "category": "U.S. NEWS", "short_description": "Health experts said it is too early to predict whether demand would match up with the 171 million doses of the new boosters the U.S. ordered for the fall.", "authors": "Carla K. Johnson, AP", "date": "2022-09-23"}
{"link": "https://www.huffpost.com/entry/american-airlines-passenger-banned-flight-attendant-punch-justice-department_n_632e25d3e4b0e247890329fe", "headline": "American Airlines Flyer Charged, Banned For Life After Punching Flight Attendant On Video", "category": "U.S. NEWS", "short_description": "He was subdued by passengers and crew when he fled to the back of the aircraft after the confrontation, according to the U.S. attorney's office in Los Angeles.", "authors": "Mary Papenfuss", "date": "2022-09-23"}
{"link": "https://www.huffpost.com/entry/funniest-tweets-cats-dogs-september-17-23_n_632de332e4b0695c1d81dc02", "headline": "23 Of The Funniest Tweets About Cats And Dogs This Week (Sept. 17-23)", "category": "COMEDY", "short_description": "\"Until you have a dog you don't understand what could be eaten.\"", "authors": "Elyse Wanshel", "date": "2022-09-23"}
```

**Observation:** Format confirmed correct — each line is a valid JSON object with all expected fields present. Records are from September 2022.

---

## Step 4: Setting Up Hadoop with Docker

### Goal
Run Hadoop locally using Docker to process the news dataset using MapReduce.

### First Attempt — sequenceiq/hadoop-docker:2.7.0

This is a commonly referenced image for Hadoop in tutorials and older course materials.

**Command tried:**
```bash
docker pull sequenceiq/hadoop-docker:2.7.0
```

**Error:**
```
Error response from daemon: not implemented: media type
"application/vnd.docker.distribution.manifest.v1+prettyjws" is no longer
supported since containerd v2.1, please rebuild the image as
"application/vnd.docker.distribution.manifest.v2+json" or
"application/vnd.oci.image.manifest.v1+json"
```

**Root cause:** `sequenceiq/hadoop-docker` is an old, unmaintained image built with Docker manifest v1 format, which was dropped in containerd v2.1 (shipped with newer Docker Desktop versions). The image cannot be pulled anymore on modern Docker installs.

### Decision — Switch to apache/hadoop:3

After hitting the above error, we evaluated three alternatives:

| Option | Reason considered | Why chosen/rejected |
|--------|-------------------|---------------------|
| `apache/hadoop:3` | Official Apache image, actively maintained | **Chosen** — most reliable, up-to-date |
| `bde2020/hadoop-namenode` | Popular in courses, multi-container setup | Skipped — requires docker-compose with multiple containers, more complex for now |
| `bitnami/hadoop` | Well maintained by Bitnami/VMware | Skipped — heavier, more opinionated config |

`apache/hadoop:3` was chosen because it is the official image, uses modern manifest format, and is simple to get running for a single-node setup.

**Command:**
```bash
docker pull apache/hadoop:3
```

**Result:** Pull successful.
```
Status: Downloaded newer image for apache/hadoop:3
docker.io/apache/hadoop:3
Digest: sha256:af361b20bec0dfb13f03279328572ba764926e918c4fe716e197b8be2b08e37f
```

All 23 layers downloaded and extracted successfully.

---

## Step 5: Configure and Start HDFS Inside Docker

### Problem — Hadoop not configured for HDFS
When trying to start the namenode, it failed with:
```
Invalid URI for NameNode address (check fs.defaultFS): file:/// has no authority.
```
The `apache/hadoop:3` image ships with a blank `core-site.xml`, so `fs.defaultFS` defaulted to `file:///` (local filesystem) instead of HDFS.

### Fix — Write Hadoop config files inside the container
Wrote two config files directly into the container at `/opt/hadoop/etc/hadoop/`:

**core-site.xml** — sets the default filesystem to HDFS:
```xml
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://localhost:9000</value>
  </property>
</configuration>
```

**hdfs-site.xml** — sets replication factor to 1 (single node) and data directories:
```xml
<configuration>
  <property><name>dfs.replication</name><value>1</value></property>
  <property><name>dfs.namenode.name.dir</name><value>/tmp/hadoop/namenode</value></property>
  <property><name>dfs.datanode.data.dir</name><value>/tmp/hadoop/datanode</value></property>
</configuration>
```

Then formatted the namenode and started daemons:
```bash
hdfs namenode -format -force
hdfs --daemon start namenode
hdfs --daemon start datanode
```

Verified HDFS was healthy via `hdfs dfsadmin -report` — capacity, replication, and block status all clean.

### Problem — No SSH in container
`start-dfs.sh` uses SSH to start nodes, but the container has no SSH daemon.

**Fix:** Started namenode and datanode directly with `hdfs --daemon start` instead of using `start-dfs.sh`.

---

## Step 6: Upload Data to HDFS

With HDFS running, the `news_headlines.txt` file (mounted into the container at `/data/`) was uploaded to HDFS.

**Commands run:**
```bash
# List HDFS root
hdfs dfs -ls /

# Create input directory
hdfs dfs -mkdir -p /user/hadoop/input

# Upload file from container local mount to HDFS
hdfs dfs -put /data/news_headlines.txt /user/hadoop/input/

# Verify upload
hdfs dfs -ls /user/hadoop/input/
```

**Output of final ls:**
```
Found 1 items
-rw-r--r--   1 hadoop supergroup    2085518 2026-03-07 03:55 /user/hadoop/input/news_headlines.txt
```

File is in HDFS: 2,085,518 bytes (~2 MB), 5000 records, replication factor 1.

**How the file got into the container:** The Docker container was started with a volume mount:
```bash
docker run -d --name hadoop-hw2 \
  -v "/Users/anees/Documents/DATA228/Homeworks /HW2/news_headlines.txt:/data/news_headlines.txt" \
  apache/hadoop:3 tail -f /dev/null
```
This made the local file available inside the container at `/data/news_headlines.txt`, from where it was pushed into HDFS.

---

## Step 7: Write MapReduce Job — word_frequency.py

**File:** `word_frequency.py`
**Framework:** `mrjob` (Python MapReduce library that can run locally or on Hadoop)

**Dependencies installed:**
```bash
pip install mrjob nltk
python -c "import nltk; nltk.download('stopwords')"
```

**What the job does (2-step MapReduce):**

- **Step 1 — Mapper:** Parses each JSON line, extracts the `headline` field, lowercases it, strips punctuation, filters out NLTK English stopwords and words shorter than 3 characters, emits `(word, 1)` for each valid word.
- **Step 1 — Reducer:** Sums all counts per word → `(word, total_count)`
- **Step 2 — Mapper:** Re-emits everything as `(None, (count, word))` to funnel all data to a single reducer for global sorting
- **Step 2 — Reducer:** Sorts all `(count, word)` pairs descending, takes top 50, emits `(word, count)`

---

## Step 8: Test Locally

Before running on Hadoop, the job was tested locally using mrjob's built-in local runner.

**Command:**
```bash
python word_frequency.py news_headlines.txt
```

**Result — Top 50 words from 5000 headlines:**
```
"trump"         532
"covid"         290
"biden"         268
"says"          248
"new"           225
"trumps"        153
"gop"           152
"house"         122
"donald"        114
"coronavirus"   113
"joe"           110
"first"         100
"police"         97
"tweets"         91
"white"          90
"week"           85
"election"       85
"news"           81
"ukraine"        80
"vaccine"        78
"twitter"        78
"court"          78
"people"         76
"black"          76
"calls"          75
"fox"            74
"texas"          73
"man"            72
"get"            71
"dead"           71
"jan"            69
"years"          66
"funniest"       65
"day"            65
"death"          64
"best"           64
"russian"        62
"say"            61
"reveals"        61
"report"         61
"dies"           61
"video"          60
"republicans"    60
"million"        60
"capitol"        60
"bill"           60
"school"         59
"pandemic"       59
"make"           59
"gets"           59
```

**Observations:**
- "trump" (532) is the most frequent word by a large margin — consistent with HuffPost's political coverage in 2022.
- "covid" (290), "biden" (268), "ukraine" (80), "vaccine" (78) reflect the dominant news themes of the period.
- Stopword filtering is working correctly — common words like "the", "and", "is" are absent.
- Local test passed with no errors. Ready to run on Hadoop.

---

## Step 9: Run on Hadoop Cluster (inside Docker)

### Issues encountered and fixed

**Issue 1 — YARN not running**
mrjob's `hadoop` runner requires YARN (ResourceManager + NodeManager). Only HDFS was running. Fixed by writing `mapred-site.xml` and `yarn-site.xml` and starting YARN daemons:
```bash
yarn --daemon start resourcemanager
yarn --daemon start nodemanager
```

**Issue 2 — MRAppMaster not found**
```
Error: Could not find or load main class org.apache.hadoop.mapreduce.v2.app.MRAppMaster
```
Root cause: `HADOOP_MAPRED_HOME` was not set in the task environment. Fixed by adding to `mapred-site.xml`:
```xml
<property><name>yarn.app.mapreduce.am.env</name><value>HADOOP_MAPRED_HOME=/opt/hadoop</value></property>
<property><name>mapreduce.map.env</name><value>HADOOP_MAPRED_HOME=/opt/hadoop</value></property>
<property><name>mapreduce.reduce.env</name><value>HADOOP_MAPRED_HOME=/opt/hadoop</value></property>
```

**Issue 3 — NLTK stopwords not found on YARN worker**
```
LookupError: Resource stopwords not found.
Searched in: '/home/nltk_data', '/usr/nltk_data', '/usr/share/nltk_data' ...
```
Root cause: NLTK data was downloaded to `/opt/hadoop/nltk_data` (hadoop user home), but YARN task containers look for it in system paths. Fixed by downloading to a system-wide location:
```bash
python3 -c "import nltk; nltk.download('stopwords', download_dir='/usr/local/share/nltk_data')"
```

**Issue 4 — YARN job stuck in ACCEPTED state**
Root cause: NodeManager had no memory/vcores configured, so the scheduler couldn't allocate containers. Fixed by adding to `yarn-site.xml`:
```xml
<property><name>yarn.nodemanager.resource.memory-mb</name><value>4096</value></property>
<property><name>yarn.nodemanager.resource.cpu-vcores</name><value>4</value></property>
<property><name>yarn.nodemanager.vmem-check-enabled</name><value>false</value></property>
```

### Final command
```bash
python3 /tmp/word_frequency.py \
  -r hadoop \
  --hadoop-bin /opt/hadoop/bin/hadoop \
  hdfs:///user/hadoop/input/news_headlines.txt
```

### Result — Both MapReduce steps completed successfully

**Step 1** (word count): 5000 input records → 39,844 map output records → 10,421 unique words
**Step 2** (top-50 sort): 10,421 input records → 50 output records

**MapReduce counters (Step 1):**
- Map input records: 5,000
- Map output records: 39,844
- Reduce input groups (unique words): 10,421
- HDFS bytes read: 2,089,834

**Output matches local run exactly:**
```
"trump"     532       "white"  90    "fox"    74
"covid"     290       "week"   85    "texas"  73
"biden"     268       "election" 85  "man"    72
"says"      248       "news"   81    ...
```

Results confirmed correct — Hadoop cluster output is identical to local test output.

---

## Step 10: Key Findings from Hadoop Output

**Finding 1 — Politics dominates the news cycle**
The top 10 words are almost entirely political: "trump" (532), "biden" (268), "gop" (152), "house" (122), "donald" (114), "joe" (110), "election" (85). "trump" alone appears in over 10% of all 5000 headlines. This reflects HuffPost's strong political focus and the intensity of US political coverage in 2022.

**Finding 2 — COVID and the pandemic remain a top-3 theme**
"covid" (290) and "coronavirus" (113) together appear in ~8% of headlines, and "vaccine" (78) and "pandemic" (59) add to this. Despite being nearly 3 years into the pandemic by September 2022, it was still a dominant news topic — driven by the Omicron booster rollout visible in the very first headline in the dataset.

**Finding 3 — Jan 6 and the Capitol still in the news in 2022**
"jan" (69) and "capitol" (60) appear frequently and together point specifically to ongoing Jan 6 coverage — investigations, hearings, and prosecutions were active throughout 2022. "court" (78) and "republicans" (60) reinforce this theme of political-legal proceedings still dominating the national conversation.

---

## Step 11: Reflection on Challenges and Learnings

### Challenges

**1. Deprecated Docker image**
The course-referenced `sequenceiq/hadoop-docker:2.7.0` image is no longer usable with modern Docker. This is a common real-world problem — older images built with Docker manifest v1 break silently on newer Docker Desktop versions. The fix was to switch to the official `apache/hadoop:3` image.

**2. Blank Hadoop config in official image**
The `apache/hadoop:3` image ships with empty config files — it is designed to be configured by the user. Setting up `core-site.xml`, `hdfs-site.xml`, `mapred-site.xml`, and `yarn-site.xml` manually gave a much deeper understanding of how Hadoop's components fit together than a pre-configured image would have.

**3. No SSH in container**
Standard Hadoop startup scripts use SSH to start daemons across nodes. In a minimal container, SSH is not installed. Starting daemons directly with `hdfs --daemon start` and `yarn --daemon start` is the workaround — and actually more transparent about what services are running.

**4. YARN resource allocation**
Without explicit memory and vcore configuration, the NodeManager registers with zero resources and the scheduler cannot assign any containers — jobs sit in ACCEPTED state forever. This was non-obvious to debug and required reading YARN scheduler internals.

**5. NLTK data path in YARN tasks**
Python libraries that rely on data files (like NLTK's stopword corpus) need those files in system-wide paths when running inside YARN containers. The hadoop user's home directory is not visible to YARN task environments. This is a general lesson: any ML/NLP dependency with external data files needs careful path management in distributed environments.

### Learnings

- Hadoop is not just one service — it is HDFS (storage) + YARN (resource management) + MapReduce (computation), each needing its own configuration.
- mrjob abstracts the Hadoop Streaming API, allowing Python MapReduce jobs without writing Java, but it still requires a fully functioning YARN cluster underneath.
- The 2-step MapReduce pattern (count → global sort) is a standard pattern for "top-N" problems: you cannot sort globally in step 1 because each reducer only sees a subset of keys.
- Local testing with mrjob before submitting to Hadoop saves significant debugging time.
- Distributed systems surface environment issues (paths, user contexts, resource limits) that never appear in local testing.

---

## Files in This Project

| File | Description |
|------|-------------|
| `News_Category_Dataset_v3.json` | Original full dataset downloaded from Kaggle |
| `news_headlines.txt` | Trimmed dataset — first 5000 lines of the original |
| `word_frequency.py` | 2-step MapReduce job to find top 50 words in headlines |
| `README.md` | This file — project log and documentation |

---

## Notes

- The dataset uses **NDJSON** (Newline Delimited JSON) format — one JSON object per line.
- `head -n` counts lines, so 5000 lines = 5000 records in this format.
