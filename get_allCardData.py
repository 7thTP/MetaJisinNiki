import pickle
from mtgsdk import Card
#cards = Card.all()
cards = Card.where(language='japanese').all()
# output bin file
with open('cardlist-ja.bin', 'wb') as f:
    pickle.dump(cards, f)