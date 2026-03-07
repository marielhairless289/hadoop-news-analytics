# Hadoop News Analytics

A distributed word frequency analysis pipeline built on a single-node Apache Hadoop cluster running inside Docker. The pipeline ingests 5,000 news headlines from HuffPost, processes them through a two-step MapReduce job written in Python using the mrjob library, and produces the top 50 most frequent meaningful words across the dataset. The project covers the full stack: data preparation, HDFS storage, YARN resource management, and MapReduce computation.

---

## Dataset

The dataset is the [HuffPost News Category Dataset](https://www.kaggle.com/datasets/rmisra/news-category-dataset) published on Kaggle by Rishabh Misra. It contains approximately 210,000 news article records spanning from 2012 to 2022, stored in NDJSON format (one JSON object per line). Each record includes the article headline, category, short description, author names, publication date, and URL.

For this project, the first 5,000 records were extracted into a working file to keep processing time reasonable while still producing statistically meaningful word frequency results.

```bash
head -n 5000 News_Category_Dataset_v3.json > news_headlines.txt
```

The choice to analyze headlines specifically rather than full article text was deliberate. Headlines are written to be dense and representative. They compress the most important information from an article into a single line, which means word frequency across thousands of headlines gives a very accurate picture of what topics were dominating news coverage at any given time.

---

## Architecture

The pipeline uses a standard single-node Hadoop setup with all four core components configured manually.

**HDFS** serves as the distributed filesystem. The input file is stored in HDFS at `/user/hadoop/input/` and the MapReduce job reads directly from there. Even in a single-node setup, HDFS provides the block-based storage abstraction that Hadoop's MapReduce framework depends on.

**YARN** (Yet Another Resource Negotiator) manages resource allocation for the MapReduce job. The ResourceManager accepts job submissions and the NodeManager executes the map and reduce tasks in containers with allocated CPU and memory.

**MapReduce** is the computation layer. The job is written in Python using mrjob, which wraps Hadoop Streaming to allow Python functions to act as mappers and reducers without requiring Java.

**mrjob** is the Python library that abstracts Hadoop Streaming. It handles packaging the job, uploading it to HDFS, submitting it to YARN, and collecting the output.

---

## Hadoop Setup Inside Docker

Rather than using a pre-configured sandbox, the entire Hadoop cluster was configured from scratch inside the official `apache/hadoop:3` Docker container. This required writing all four Hadoop configuration files manually.

### Why apache/hadoop:3

The commonly referenced `sequenceiq/hadoop-docker:2.7.0` image is no longer usable on modern Docker installations. It was built with Docker manifest v1 format, which was dropped in containerd v2.1. Attempting to pull it produces:

```
Error response from daemon: not implemented: media type
"application/vnd.docker.distribution.manifest.v1+prettyjws"
is no longer supported since containerd v2.1
```

The official `apache/hadoop:3` image from Docker Hub uses the current manifest format and is actively maintained by the Apache Software Foundation.

### Container Setup

The container is started with a volume mount so that the local dataset file is accessible inside the container without copying it manually:

```bash
docker run -d --name hadoop-hw2 \
  -v "/path/to/news_headlines.txt:/data/news_headlines.txt" \
  apache/hadoop:3 tail -f /dev/null
```

### core-site.xml

Sets the default filesystem to HDFS. Without this, `fs.defaultFS` defaults to `file:///` and all Hadoop commands operate on the local filesystem instead of HDFS.

```xml
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://localhost:9000</value>
  </property>
</configuration>
```

### hdfs-site.xml

Configures the namenode and datanode data directories and sets replication factor to 1 since this is a single-node cluster.

```xml
<configuration>
  <property><name>dfs.replication</name><value>1</value></property>
  <property><name>dfs.namenode.name.dir</name><value>/tmp/hadoop/namenode</value></property>
  <property><name>dfs.datanode.data.dir</name><value>/tmp/hadoop/datanode</value></property>
</configuration>
```

### mapred-site.xml

Configures the MapReduce framework to use YARN and sets the `HADOOP_MAPRED_HOME` environment variable in the task container environment. Without this, YARN cannot locate `MRAppMaster` and the job fails immediately with a class-not-found error.

```xml
<configuration>
  <property><name>mapreduce.framework.name</name><value>yarn</value></property>
  <property><name>yarn.app.mapreduce.am.env</name><value>HADOOP_MAPRED_HOME=/opt/hadoop</value></property>
  <property><name>mapreduce.map.env</name><value>HADOOP_MAPRED_HOME=/opt/hadoop</value></property>
  <property><name>mapreduce.reduce.env</name><value>HADOOP_MAPRED_HOME=/opt/hadoop</value></property>
</configuration>
```

### yarn-site.xml

Configures the NodeManager with explicit memory and vcore allocations. This is a critical step that is easy to miss: by default the NodeManager registers with zero resources, and the YARN scheduler silently keeps jobs in ACCEPTED state indefinitely because no containers can be allocated.

```xml
<configuration>
  <property><name>yarn.nodemanager.aux-services</name><value>mapreduce_shuffle</value></property>
  <property><name>yarn.nodemanager.resource.memory-mb</name><value>4096</value></property>
  <property><name>yarn.nodemanager.resource.cpu-vcores</name><value>4</value></property>
  <property><name>yarn.nodemanager.vmem-check-enabled</name><value>false</value></property>
</configuration>
```

### Starting the Cluster

The standard `start-dfs.sh` and `start-yarn.sh` scripts use SSH to start services across nodes. Since the container has no SSH daemon, each service is started directly:

```bash
hdfs namenode -format -force
hdfs --daemon start namenode
hdfs --daemon start datanode
yarn --daemon start resourcemanager
yarn --daemon start nodemanager
```

### Uploading to HDFS

```bash
hdfs dfs -mkdir -p /user/hadoop/input
hdfs dfs -put /data/news_headlines.txt /user/hadoop/input/
hdfs dfs -ls /user/hadoop/input/
```

Verification output:

```
Found 1 items
-rw-r--r--   1 hadoop supergroup    2085518 2026-03-07 03:55 /user/hadoop/input/news_headlines.txt
```

---

## MapReduce Job

The job is in `word_frequency.py` and uses a two-step MapReduce pipeline.

A single MapReduce step is not sufficient for a global top-N problem. In a standard word count job, each reducer independently processes its assigned subset of keys. There is no way to determine the global top 50 within a single step because no single reducer ever sees all word counts at once. The second step solves this by routing all `(count, word)` pairs to a single reducer using `None` as the key, which forces all data through one place where a global sort can be performed.

### Step 1: Word Count

The mapper parses each line as JSON, extracts the `headline` field, lowercases the text, strips all non-alphabetic characters using a regular expression, and splits into individual words. Each word is filtered against the NLTK English stopword list and must be at least 3 characters long. For every word that passes these filters, the mapper emits `(word, 1)`.

The reducer receives all instances of each word grouped together and sums the counts, emitting `(word, total_count)`.

After Step 1, the dataset of 5,000 headlines produces 39,844 map output records and reduces to 10,421 unique words.

### Step 2: Global Sort and Top 50

The mapper re-emits every `(word, count)` pair as `(None, (count, word))`. Using `None` as the key sends everything to a single reducer.

The reducer collects all `(count, word)` pairs, sorts them in descending order, takes the top 50, and emits each as `(word, count)`.

### Running Locally

```bash
python word_frequency.py news_headlines.txt
```

### Running on Hadoop

```bash
python3 /tmp/word_frequency.py \
  -r hadoop \
  --hadoop-bin /opt/hadoop/bin/hadoop \
  hdfs:///user/hadoop/input/news_headlines.txt
```

### Job Counters

**Step 1 (Word Count)**

| Counter | Value |
|---------|-------|
| Map input records | 5,000 |
| Map output records | 39,844 |
| Reduce input groups (unique words) | 10,421 |
| HDFS bytes read | 2,089,834 |

**Step 2 (Top-50 Sort)**

| Counter | Value |
|---------|-------|
| Input records | 10,421 |
| Output records | 50 |

---

## Results

The Hadoop cluster output is identical to the local test output, confirming correctness.

| Rank | Word | Count | Rank | Word | Count |
|------|------|-------|------|------|-------|
| 1 | trump | 532 | 11 | joe | 110 |
| 2 | covid | 290 | 12 | first | 100 |
| 3 | biden | 268 | 13 | police | 97 |
| 4 | says | 248 | 14 | tweets | 91 |
| 5 | new | 225 | 15 | white | 90 |
| 6 | trumps | 153 | 16 | week | 85 |
| 7 | gop | 152 | 17 | election | 85 |
| 8 | house | 122 | 18 | news | 81 |
| 9 | donald | 114 | 19 | ukraine | 80 |
| 10 | coronavirus | 113 | 20 | vaccine | 78 |

### What the Data Shows

**Politics dominated the news cycle completely.** The top 10 words are almost entirely political figures and institutions: trump (532), biden (268), gop (152), house (122), donald (114), joe (110), election (85). The word "trump" alone appears in more than 10% of all 5,000 headlines, more than double the frequency of the second most common word. This is consistent with HuffPost's editorial focus on US political coverage and the intensity of the political environment in 2022.

**COVID was still a top-three topic in late 2022.** "covid" (290) and "coronavirus" (113) together appear in roughly 8% of headlines. "vaccine" (78) and "pandemic" (59) contribute further. Nearly three years into the pandemic, it remained a dominant subject in September 2022, driven in part by the Omicron booster rollout. The very first headline in the dataset is about four million Americans receiving Omicron-targeted COVID boosters.

**January 6 investigations were still active in the news.** "jan" (69) and "capitol" (60) together point specifically to ongoing coverage of the January 6th Capitol attack. Congressional investigations and criminal prosecutions were actively being reported throughout 2022. "court" (78) and "republicans" (60) reinforce this theme of political and legal proceedings running in parallel.

---

## Technical Challenges and Solutions

**CentOS 7 yum repositories offline.** The `apache/hadoop:3` image is based on CentOS 7, which reached end-of-life in June 2024. All default yum mirrors were taken offline, making it impossible to install packages like Python 3 using the standard `yum install` command. The fix was to manually point the yum repository configuration to the CentOS vault mirrors at `vault.centos.org`, which archive old CentOS releases.

**NLTK stopwords not found in YARN task containers.** NLTK was installed in the hadoop user's home directory and `nltk.download('stopwords')` saved data to `/opt/hadoop/nltk_data`. YARN task containers run in isolated environments and do not have access to the user's home directory. The fix was to download the NLTK data to a system-wide path that is visible to all processes:

```bash
python3 -c "import nltk; nltk.download('stopwords', download_dir='/usr/local/share/nltk_data')"
```

**YARN containers never allocated.** After configuring YARN and starting the ResourceManager and NodeManager, submitted jobs would appear in the YARN UI with status ACCEPTED but never move to RUNNING. The root cause is that the NodeManager registers with zero memory and zero vcores unless explicitly configured. The scheduler cannot allocate containers with zero capacity, so jobs wait indefinitely with no error message to indicate why. The fix was adding explicit resource values to `yarn-site.xml`.

**MRAppMaster class not found.** The first Hadoop job submission failed immediately with `Error: Could not find or load main class org.apache.hadoop.mapreduce.v2.app.MRAppMaster`. This happens because YARN task containers do not inherit the shell environment of the process that submitted the job. `HADOOP_MAPRED_HOME` must be explicitly passed into the container environment through `mapred-site.xml` configuration properties, not just set as a shell variable.

---

## Project Files

| File | Description |
|------|-------------|
| `word_frequency.py` | Two-step mrjob MapReduce job for top-50 word frequency analysis |
| `news_headlines.txt` | First 5,000 records from the HuffPost News Category Dataset |
| `README.md` | This file |

The full dataset (`News_Category_Dataset_v3.json`) and the Python virtual environment directory are excluded from the repository via `.gitignore`.
