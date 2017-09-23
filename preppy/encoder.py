from preppy.tweet_list import TweetList
from pandas import DataFrame, read_excel


class TweetEncoder(object):
    def __init__(self):
        self.tweets = TweetList()

    def encode_variable_from_excel(self, file_name, user_id):
        """
        Encode variables that were coded externally in
            excel by grad students. Store these encoded
            values in the tweet metadata dict within
            TweetList class instance
        :param file_name: name of the excel file. This excel file
            may have been written by pandas.DataFrame.to_excel().
            This excel table must contain column "id" representing
            the Tweet ID
        :param user_id: a name to assign to the encodings
        :return: NoneType
        """
        df = read_excel(file_name)
        n = df.shape[0]
        for i in range(n):
            le_row = df.iloc[i, :]
            _id_str = str(le_row.id)
            _relevance = str(le_row.relevance)
            self.tweets.record_metadata(
                id_str=_id_str,
                param="RELEVANCE",
                user_id=user_id,
                value=_relevance)
