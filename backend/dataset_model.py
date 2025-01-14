from dataclasses import dataclass, field
import pandas as pd

@dataclass
class DatasetModel:
    keypath: str = ""
    dataFrame: pd.DataFrame = field(default_factory=pd.DataFrame)
    title: str = field(init=False)

    def __post_init__(self):
        self.title = self.keypath.split('/')[-1] if self.keypath else "Untitled"

    @classmethod
    def from_values(cls, keypath: str, dataframe: pd.DataFrame):
        return cls(keypath=keypath, dataFrame=dataframe)