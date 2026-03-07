from mrjob.job import MRJob
from mrjob.step import MRStep
import re
import json
from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words('english'))

class MRWordFrequency(MRJob):

    def steps(self):
        return [
            MRStep(mapper=self.mapper_extract_words,
                   reducer=self.reducer_count_words),
            MRStep(mapper=self.mapper_prepare_sort,
                   reducer=self.reducer_top_words)
        ]

    def mapper_extract_words(self, _, line):
        try:
            data = json.loads(line)
            headline = data.get('headline', '')
        except:
            headline = line

        headline = headline.lower()
        headline = re.sub(r'[^a-z\s]', '', headline)
        words = headline.split()

        for word in words:
            if word not in STOP_WORDS and len(word) > 2:
                yield word, 1

    def reducer_count_words(self, word, counts):
        yield word, sum(counts)

    def mapper_prepare_sort(self, word, count):
        yield None, (count, word)

    def reducer_top_words(self, _, count_word_pairs):
        top = sorted(count_word_pairs, reverse=True)[:50]
        for count, word in top:
            yield word, count


if __name__ == '__main__':
    MRWordFrequency.run()
