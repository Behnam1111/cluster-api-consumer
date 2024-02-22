from abc import abstractmethod, ABC


class BaseClusterAPIConsumer(ABC):
    @abstractmethod
    async def create_group(self, group_id: str) -> bool:
        pass

    @abstractmethod
    async def delete_group(self, group_id: str) -> bool:
        pass
