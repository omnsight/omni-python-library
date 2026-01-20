class Singleton:
    """A thread-safe-ready base class for Singletons."""

    _instances: dict = {}

    def __new__(cls):
        if cls not in cls._instances:
            # Create the instance and store it in the dictionary
            instance = super(Singleton, cls).__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]

    def init(self, *args, **kwargs):
        """
        Initialize the singleton instance.
        This method is called only once when the instance is created.
        """
        pass
