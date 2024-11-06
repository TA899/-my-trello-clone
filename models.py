from . import db

class Column(db.Model):
    __tablename__ = 'columns'
    column_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Asociar la columna con el usuario
    cards = db.relationship('Card', backref='column', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Column {self.name}>'

    def to_dict(self):
        return {
            'column_id': self.column_id,
            'name': self.name,
            'user_id': self.user_id,
            'cards': [card.to_dict() for card in self.cards]
        }

class Card(db.Model):
    __tablename__ = 'cards'
    card_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    column_id = db.Column(db.Integer, db.ForeignKey('columns.column_id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Asociar la tarjeta con el usuario

    def __repr__(self):
        return f'<Card {self.title}>'

    def to_dict(self):
        return {
            'card_id': self.card_id,
            'title': self.title,
            'description': self.description,
            'column_id': self.column_id,
            'user_id': self.user_id  # Incluye user_id en la representación
        }
