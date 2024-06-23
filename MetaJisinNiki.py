from io import StringIO
from mtgsdk import Card
from collections import Counter

import pandas as pd
import numpy as np
import pickle
import re
import MeCab

def main(TP):
    # open cardlist.bin
    with open('cardlist.bin', 'rb') as f:
        cards = pickle.load(f)

    print('input data path')
    dl = get_kingyoDeckList(TP)  # get Kingyo format data
    df_d = listToPD(dl)  # Reformat list
    deck = [nameToCardData(item['name'], cards) for index, item in df_d.iterrows()]  # Get deck card data
    df_mana = pd.DataFrame(index=[], columns=['number'])
    sentence = ''

    for card in deck:
        #print(card.name)
        df_mana.loc[card.name] = 0
        if '//' in card.name:  # Trap double-faced cards
            dfc = splitDoubleFaceCard(card.name)
            df_mana.at[card.name, 'number'] = df_d.at[df_d.index[df_d['name'] == dfc[0]].tolist()[0], 'number']
        else:
            df_mana.at[card.name, 'number'] = df_d.at[df_d.index[df_d['name'] == card.name].tolist()[0], 'number']
        if card.original_text:
            sentence = sentence + ' ' + card.original_text

    #Count品詞
    tagger = MeCab.Tagger()
    buffer = StringIO(tagger.parse(sentence))

    df = pd.read_csv(
        buffer,
        names=["表層形", "品詞", "品詞細分類1", "品詞細分類2", "品詞細分類3", "活用型", "活用形", "原形", "読み",
               "発音"],
        skipfooter=1,
        sep="[\t,,]",
        engine="python",
    )
    noun_df = df.query("品詞=='名詞'")
    noun_counter = dict()

    for word in noun_df["表層形"]:
        if noun_counter.get(word):
            noun_counter[word] += 1
        else:
            noun_counter[word] = 1

    c = Counter(noun_df["表層形"])
    print(c.most_common(20))


def get_kingyoDeckList(TP):
    dl = []
    with open(TP, "r", encoding='UTF-8') as file:
        for i in file:
            dl.append(i.rstrip('\n'))
    return dl


def listToPD(dl):  # MTG decklist format re-format ['number', 'name']
    dl2 = []
    for l in dl:
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
        return 'not found'
    else:
        return 0


def manaSplit(manaCost):
    op = []
    gm = 0
    manas = re.findall("(?<=\{).+?(?=\})", manaCost)
    for mana in manas:
        if mana.isdigit():
            gm = int(mana)
        else:
            op.append(mana)
    if gm:
        op[0:0] = ['GM'] * gm
    return op


def splitDoubleFaceCard(name):
    return name.split(' // ')


if __name__ == "__main__":
    TP = r'C:\temp\Deck.txt'  # inport deck data
    main(TP)
