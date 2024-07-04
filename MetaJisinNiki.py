from io import StringIO
from mtgsdk import Card
from collections import Counter

import pandas as pd
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
    sentence = ''
    for deck_path in file_list:
        dl = get_kingyoDeckList(deck_path)  # get Kingyo format data
        df_d = listToPD(dl)  # Reformat list
        deck = [nameToCardData(item['name'], cards) for index, item in df_d.iterrows()]  # Get deck card data
        #df_mana = pd.DataFrame(index=[], columns=['number'])
        print('inport :' + deck_path)
        for card in deck:
            if not card:
                continue
            #print(card.name)
            # if '//' in card.name:  # Trap double-faced cards
            #    df_mana.at[card.name, 'number'] = df_d.at[df_d.index[df_d['name'] == dfc[0]].tolist()[0], 'number']
            # else:
            #    df_mana.at[card.name, 'number'] = df_d.at[df_d.index[df_d['name'] == card.name].tolist()[0], 'number']
            if card.foreign_names:
                for fore in card.foreign_names:
                    if fore['language'] == 'Japanese':
                        if 'text' in fore:
                            sentence = margeStr(sentence, fore['text'])
                        break

            else:
                sentence = margeStr(sentence, card.text)

    # Count品詞
    tagger = MeCab.Tagger()
    # 記号削除
    sentence = re.sub(r"[!#$%&)*+,./:;?@^_`|{}~「」〔〕“”〈〉『』【】＆＊・（）＄＃＠。？！｀＋￥％]", '', sentence)
    buffer = StringIO(tagger.parse(sentence))

    df = pd.read_csv(
        buffer,
        names=["表層形", "品詞", "品詞細分類1", "品詞細分類2", "品詞細分類3", "活用型", "活用形", "原形", "読み",
               "発音"],
        skipfooter=1,
        sep="[\t,,]",
        engine="python",
    )
    #noun_df = df.query("品詞=='名詞'")
    noun_counter = dict()

    for word in df["表層形"]:
        if noun_counter.get(word):
            noun_counter[word] += 1
        else:
            noun_counter[word] = 1

    c = Counter(df["表層形"])
    print(c.most_common(50))


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
