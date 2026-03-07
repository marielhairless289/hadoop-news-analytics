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
