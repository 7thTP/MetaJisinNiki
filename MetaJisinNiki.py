from io import StringIO
from mtgsdk import Card
from collections import Counter

import pandas as pd
import numpy as np
import pickle
import re
import MeCab
import os
import glob


def main():
    # open cardlist.bin
    with open('cardlist-ja.bin', 'rb') as f:
        cards = pickle.load(f)

    print('input data path')
    # inport decks
    dir_path = "./decks/"
    file_list = glob.glob(os.path.join(dir_path, "*.txt"))
    sentence = {}
    type_n = {}
    deck_n = 0
    for deck_path in file_list:
        deck_n = deck_n + 1
        # get Kingyo format data
        dl = get_kingyoDeckList(deck_path)
        # Reformat list
        df_d = listToPD(dl)
        # Get deck card data
        deck = [nameToCardData(item['name'], cards) for index, item in df_d.iterrows()]
        print('inport :' + deck_path)
        for card in deck:
            # failed data trap
            if not card:
                continue

            # append card text
            if card.foreign_names:
                # search 'Japanese' loop
                for foreign in card.foreign_names:
                    if foreign['language'] == 'Japanese':
                        # check text is not brank
                        if 'text' in foreign:
                            # dict key check
                            if sentence.get(card.types[0]):
                                sentence[card.types[0]] = margeStr(sentence[card.types[0]], foreign['text'])
                                type_n[card.types[0]] = type_n[card.types[0]] + 1
                            else:
                                sentence[card.types[0]] = margeStr('', foreign['text'])
                                type_n[card.types[0]] = 1
                        break

            else:
                # dict key check
                if sentence.get(card.types[0]):
                    sentence[card.types[0]] = margeStr(sentence[card.types[0]], card.text)
                    type_n[card.types[0]] = type_n[card.types[0]] + 1
                else:
                    sentence[card.types[0]] = margeStr('', card.text)
                    type_n[card.types[0]] = 1

    print('カード効果テキスト中の頻出単語 (deck n=', deck_n, ')')
    for card_type in sentence:
        print(card_type, '(n=', type_n[card_type], ')')

        # MeCab process start
        tagger = MeCab.Tagger()
        # 記号削除
        sentence[card_type] = re.sub(r"[!#$%&)*+,./:;?@^_`|{}~「」〔〕“”〈〉『』【】＆＊・（）＄＃＠。？！｀＋￥％]", '', sentence[card_type])
        buffer = StringIO(tagger.parse(sentence[card_type]))
        df = pd.read_csv(
            buffer,
            names=["表層形", "品詞", "品詞細分類1", "品詞細分類2", "品詞細分類3", "活用型", "活用形", "原形", "読み",
                   "発音"],
            skipfooter=1,
            sep="[\t,,]",
            engine="python",
        )
        # MeCab process end

        noun_df = df.query("品詞=='名詞'")
        # Count Mono
        c = Counter(noun_df["表層形"])
        print(' ', c.most_common(10))

        # Count Bi
        print(' [bi-gram]')
        # 先頭の1列を選択 1次元配列（NumPy配列）に変換
        surface_column = noun_df["表層形"].to_numpy()
        noun_array_counter = dict()
        bi_gram = n_gram(surface_column, 2)
        bi_gram_array = []
        for word in bi_gram:
            bi_gram_array.append(word[0] + ' ' + word[1])
        c = Counter(bi_gram_array)
        print('   ', c.most_common(10))

        # Count Tri
        print(' [tri-gram]')
        noun_array_counter = dict()
        tri_gram = n_gram(surface_column, 3)
        tri_gram_array = []
        for word in tri_gram:
            tri_gram_array.append(word[0] + ' ' + word[1] + ' ' + word[2])
        c = Counter(tri_gram_array)
        print('   ', c.most_common(10))


def n_gram(target, n):
    # 基準を1[文字/単語]ずつずらしながらn文字分抜き出す
    return [target[idx:idx + n] for idx in range(len(target) - n + 1)]


def get_kingyoDeckList(TP):
    dl = []
    with open(TP, "r", encoding='UTF-8') as file:
        for i in file:
            dl.append(i.rstrip('\n'))
    return dl


def listToPD(dl):  # MTG decklist format re-format ['number', 'name']
    dl2 = []
    for l in dl:
        if l:
            dl2.append(l.split(' ', 1))
    dfDeck = pd.DataFrame(dl2, columns=['number', 'name'])
    return dfDeck


def nameToCardData(c_name, cards):
    if c_name:
        for card in cards:
            if '//' in card.name:  # Processing double-faced cards
                dfc = splitDoubleFaceCard(card.name)
                if c_name in dfc:
                    return card
            elif card.name == c_name:  # Processing one-faced cards
                return card
        return False
    else:
        return False


def splitDoubleFaceCard(name):
    return name.split(' // ')


# Check addStr type and marge strings between space
def margeStr(sorceStr, addStr):
    if type(addStr) == str:
        return sorceStr + ' ' + addStr
    else:
        return sorceStr


if __name__ == "__main__":
    main()
