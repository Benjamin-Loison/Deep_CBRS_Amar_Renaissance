import random
import itertools as it
import collections

import numpy as np
from tensorflow.keras import utils
from scipy import sparse


class UserItemEmbeddings(utils.Sequence):
    def __init__(
            self,
            ratings,
            users,
            items,
            embeddings,
            batch_size=512,
            shuffle=False,
            seed=42
    ):
        """
        Initialize a sequence of User-Item embeddings.

        :param ratings: A numpy array of triples (UserID, ItemID, Rating).
        :param users: The original users identifiers.
        :param items: The original items identifiers.
        :param embeddings: A numpy array that maps UserID and ItemID to embeddings.
        :param batch_size: The batch size.
        :param shuffle: Whether to shuffle the sequence.
        :param seed: The seed value used to shuffle the sequence.
        """
        super().__init__()
        self.ratings = ratings
        self.users = users
        self.items = items
        self.embeddings = embeddings

        # Set other settings
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed
        self.indexes = None
        self.random_state = None
        self.on_epoch_end()

    def __len__(self):
        """
        Get the number of batches.

        :return: The number of batches.
        """
        return int(np.ceil(len(self.ratings) / self.batch_size))

    def __getitem__(self, idx):
        """
        Get the i-th batch consisting of User-Item embeddings and the ratings.

        :param idx: The index of the batch.
        :return: A pair consisting of User-Item embeddings and the ratings.
        """
        batch_idx = idx * self.batch_size
        batch_off = min(batch_idx + self.batch_size, len(self.ratings))
        if self.shuffle:
            ratings = self.ratings[self.indexes[batch_idx:batch_off]]
        else:
            ratings = self.ratings[batch_idx:batch_off]
        user_embeddings = self.embeddings[ratings[:, 0]]
        item_embeddings = self.embeddings[ratings[:, 1]]
        return (user_embeddings, item_embeddings), ratings[:, 2]

    def on_epoch_end(self):
        """
        Shuffles the indexes at the end of every epoch.
        """
        if self.shuffle:
            if self.random_state is None:
                self.random_state = np.random.RandomState(self.seed)
            self.indexes = np.arange(len(self.ratings))
            self.random_state.shuffle(self.indexes)


class HybridUserItemEmbeddings(utils.Sequence):
    def __init__(
            self,
            ratings,
            users,
            items,
            graph_embeddings,
            bert_embeddings,
            batch_size=512,
            shuffle=False,
            seed=42
    ):
        """
        Initialize a sequence of Hybrid (Graph+BERT) User-Item embeddings.

        :param ratings: A numpy array of triples (UserID, ItemID, Rating).
        :param users: The original users identifiers.
        :param items: The original items identifiers.
        :param graph_embeddings: A numpy array that maps UserID and ItemID to Graph embeddings.
        :param bert_embeddings: A numpy array that maps UserID and ItemID to BERT embeddings.
        :param batch_size: The batch size.
        :param shuffle: Whether to shuffle the sequence.
        :param seed: The seed value used to shuffle the sequence.
        """
        super().__init__()
        self.ratings = ratings
        self.users = users
        self.items = items

        # Initialize both Graph and BERT embeddings sequences
        self.graph_embeddings = UserItemEmbeddings(
            ratings, users, items, graph_embeddings,
            batch_size=batch_size, shuffle=shuffle, seed=seed
        )
        self.bert_embeddings = UserItemEmbeddings(
            ratings, users, items, bert_embeddings,
            batch_size=batch_size, shuffle=shuffle, seed=seed
        )

    def __len__(self):
        """
        Get the number of batches.

        :return: The number of batches.
        """
        return len(self.graph_embeddings)

    def __getitem__(self, idx):
        """
        Get the i-th batch consisting of User-Item Graph+BERT embeddings and the ratings.

        :param idx: The index of the batch.
        :return: A pair consisting of User-Item Graph+BERT embeddings and the ratings.
        """
        (user_graph_embeddings, item_graph_embeddings), ratings = self.graph_embeddings[idx]
        (user_bert_embeddings, item_bert_embeddings), _ = self.bert_embeddings[idx]
        return (user_graph_embeddings, item_graph_embeddings, user_bert_embeddings, item_bert_embeddings), ratings

    def on_epoch_end(self):
        """
        Calls on_epoch_end() to any sub-sequence.
        """
        self.graph_embeddings.on_epoch_end()
        self.bert_embeddings.on_epoch_end()


class UserItemGraph(utils.Sequence):
    def __init__(
            self,
            ratings,
            users,
            items,
            adj_matrix,
            batch_size=512,
            shuffle=False,
            seed=42
    ):
        """
        Initialize a sequence of Graph User-Item IDs.

        :param ratings: A numpy array of triples (UserID, ItemID, Rating).
        :param users: The original users identifiers.
        :param items: The original items identifiers.
        :param adj_matrix: The adjacency matrix.
        :param batch_size: The batch size.
        :param shuffle: Whether to shuffle the sequence.
        :param seed: The seed value used to shuffle the sequence.
        """
        super().__init__()
        self.ratings = ratings
        self.users = users
        self.items = items
        self.adj_matrix = adj_matrix

        # Set other settings
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed
        self.indexes = None
        self.random_state = None
        self.on_epoch_end()

    def __len__(self):
        """
        Get the number of batches.

        :return: The number of batches.
        """
        return int(np.ceil(len(self.ratings) / self.batch_size))

    def __getitem__(self, idx):
        """
        Get the i-th batch consisting of User-Item IDs and the ratings.

        :param idx: The index of the batch.
        :return: A pair consisting of User-Item IDs and the ratings.
        """
        batch_idx = idx * self.batch_size
        batch_off = min(batch_idx + self.batch_size, len(self.ratings))
        if self.shuffle:
            ratings = self.ratings[self.indexes[batch_idx:batch_off]]
        else:
            ratings = self.ratings[batch_idx:batch_off]
        return (ratings[:, 0], ratings[:, 1]), ratings[:, 2]

    def on_epoch_end(self):
        """
        Shuffles the indexes at the end of every epoch.
        """
        if self.shuffle:
            if self.random_state is None:
                self.random_state = np.random.RandomState(self.seed)
            self.indexes = np.arange(len(self.ratings))
            self.random_state.shuffle(self.indexes)


class UserItemGraphPosNegSample(utils.Sequence):
    def __init__(
            self,
            ratings,
            users,
            items,
            adj_matrix,
            batch_size=512,
            seed=42,
            sample_size=10
    ):
        """
        Initialize a sequence of Graph User-Item IDs.

        :param ratings: A numpy array of triples (UserID, ItemID, Rating).
        :param users: The original users identifiers.
        :param items: The original items identifiers.
        :param adj_matrix: The adjacency matrix.
        :param batch_size: The batch size.
        :param seed: The seed value used to shuffle the sequence.
        :param sample_size: sample size of items for each user.
        """
        super().__init__()
        self.ratings = ratings
        self.users = users
        self.items = items
        pos_adj_dict = {k: v for k, v in adj_matrix.todok().items() if v == 1}
        neg_adj_dict = {k: v for k, v in adj_matrix.todok().items() if v == 0}
        if len(neg_adj_dict) == 0:
            raise ValueError('Negative ratings are needed!!!')

        pos_adj_matrix = sparse.coo_matrix((list(pos_adj_dict.values()), list(zip(*pos_adj_dict.keys()))),
                                           shape=adj_matrix.shape, dtype=adj_matrix.dtype
                                           )
        self.adj_matrix = pos_adj_matrix

        # Set other settings
        self.batch_size = batch_size
        self.seed = seed
        self.random_state = np.random.RandomState(seed)
        # Group positive and negative items for each user
        pos_dict = {k: [item for user, item in v] for k, v in
                    it.groupby(sorted(pos_adj_dict.keys(), key=lambda x: x[0]), key=lambda x: x[0])}
        neg_dict = {k: [item for user, item in v] for k, v in
                    it.groupby(sorted(neg_adj_dict.keys(), key=lambda x: x[0]), key=lambda x: x[0])}

        def sample_negatives(user, positives):
            negatives = neg_dict.get(user)
            if negatives:
                return negatives
            return self.random_state.choice(list(set(self.items) - set(positives)), size=sample_size)

        self.user_item_dict = {user: (pos_dict[user], sample_negatives(user, pos_dict[user]))
                               for user in users}

    def __getitem__(self, idx):
        """
        Get a sampled pair of positive and negative items for a batch of users

        :param idx: The index of the batch.
        :return: A pair consisting of User-Item IDs and the ratings.

        """
        batch_users = self.random_state.choice(self.users, size=self.batch_size // 2)
        pos_ratings = [(user, self.random_state.choice(self.user_item_dict[user][0], 1), 1) for user in batch_users]
        neg_ratings = [(user, self.random_state.choice(self.user_item_dict[user][1], 1), 0) for user in batch_users]
        pos_ratings.extend(neg_ratings)
        ratings = np.array(pos_ratings, dtype='int32')
        return (ratings[:, 0], ratings[:, 1]), ratings[:, 2]

    def __len__(self):
        """
        Get the number of batches.

        :return: The number of batches.
        """
        return int(np.ceil(len(self.ratings) / self.batch_size))


class UserItemGraphEmbeddings(utils.Sequence):
    def __init__(
            self,
            ratings,
            users,
            items,
            adj_matrix,
            embeddings,
            batch_size=512,
            shuffle=False,
            seed=42,
    ):
        """
        Initialize a sequence of Graph User-Item IDs and embeddings (e.g. BERT embeddings).

        :param ratings: A numpy array of triples (UserID, ItemID, Rating).
        :param users: The original users identifiers.
        :param items: The original items identifiers.
        :param adj_matrix: The adjacency matrix.
        :param embeddings: A numpy array that maps UserID and ItemID to embeddings.
        :param batch_size: The batch size.
        :param shuffle: Whether to shuffle the sequence.
        :param seed: The seed value used to shuffle the sequence.
        """
        super().__init__()
        self.ratings = ratings
        self.users = users
        self.items = items
        self.adj_matrix = adj_matrix

        # Initialize both Graph and embeddings sequences
        self.graph_ids = UserItemGraph(
            ratings, users, items, adj_matrix,
            batch_size=batch_size, shuffle=shuffle, seed=seed
        )
        self.embeddings = UserItemEmbeddings(
            ratings, users, items, embeddings,
            batch_size=batch_size, shuffle=shuffle, seed=seed
        )

    def __len__(self):
        """
        Get the number of batches.

        :return: The number of batches.
        """
        return len(self.graph_ids)

    def __getitem__(self, idx):
        """
        Get the i-th batch consisting of User-Item IDs, the associated embeddings, and the ratings.

        :param idx: The index of the batch.
        :return: A pair consisting of User-Item IDs, the associated embeddings, and the ratings.
        """
        (user_ids, item_ids), ratings = self.graph_ids[idx]
        (user_embeddings, item_embeddings), _ = self.embeddings[idx]
        return (user_ids, item_ids, user_embeddings, item_embeddings), ratings

    def on_epoch_end(self):
        """
        Calls on_epoch_end() to any sub-sequence.
        """
        self.graph_ids.on_epoch_end()
        self.embeddings.on_epoch_end()
