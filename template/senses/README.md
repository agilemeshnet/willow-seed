# Senses

The Sensorium - how your agent perceives the world.

Start with none. Add senses as you need them. Each sense is a simple loop:
perceive -> score attention -> act (or don't).

## Example senses (add as needed):

- **Clock** - time-based triggers ("it's 9am, check email")
- **Telegram** - receive messages from your human
- **Email** - monitor inbox for relevant messages
- **File watcher** - detect changes in specific directories
- **Web** - monitor URLs for changes
- **Graph** - detect changes in the knowledge graph

## The pattern:

```python
class MySense:
    def perceive(self):
        """Check the world. Return observations or None."""
        pass

    def score(self, observation):
        """How important is this? 0.0 to 1.0"""
        pass
```

Senses feed observations into the agent's attention system.
High-scoring observations get acted on. Low-scoring ones get noted.
The human sets the thresholds.
