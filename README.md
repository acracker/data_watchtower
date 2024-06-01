# data-watchtower

A data verification tool.
Detect issues before your CTO does.

## Installation

Install via pip:
```
pip install data-watchtower
```

## Data Loader

Loads data into memory for validation by checkers.

## Validators

Validate whether the loaded data meets expectations.

### Built-in Validators

- ExpectColumnValuesToNotBeNull
- ExpectColumnRecentlyUpdated
- ExpectColumnStdToBeBetween
- ExpectColumnMeanToBeBetween
- ExpectColumnNullRatioToBeBetween
- ExpectRowCountToBeBetween
- ExpectColumnDistinctValuesToContainSet
- ExpectColumnDistinctValuesToEqualSet
- More...

### Custom Loaders

Support for tailor-made loaders to handle specific data sources.

## Macros

Custom macros enable referencing variables like dates or config files within monitoring tasks.

### Scope of Effect

Applies to Watchtower names, checker parameters, and loader configurations.

### Custom Macros

Leverage personalized macros for dynamic content insertion.

## Supported Databases

- MySQL
- PostgreSQL
- SQLite
- And more...

## TODO

- web frontend

## Example

```python
import datetime
from data_watchtower import DbServices, Watchtower, DatabaseLoader, ExpectRowCountToBeBetween,
    ExpectColumnValuesToNotBeNull

# Database URLs
dw_test_data_db_url = "sqlite:///test.db"
dw_backend_db_url = "sqlite:///data.db"

# Custom Macro Definitions
custom_macro_map = {
    'today': {'impl': lambda: datetime.datetime.today().strftime("%Y-%m-%d")},
    'start_date': '2024-04-01',
    'column': 'name',
}

# Configure Data Loader
query = "SELECT * FROM score WHERE date='${today}'"
data_loader = DatabaseLoader(query=query, connection=dw_test_data_db_url)
data_loader.load()

# Instantiate Watchtower
wt = Watchtower(name='Score Data of ${today}', data_loader=data_loader, custom_macro_map=custom_macro_map)

# Add Validators
row_count_params = ExpectRowCountToBeBetween.Params(min_value=20)
wt.add_validator(ExpectRowCountToBeBetween(row_count_params))

null_check_params = ExpectColumnValuesToNotBeNull.Params(column='${column}')
wt.add_validator(ExpectColumnValuesToNotBeNull(null_check_params))

# Execute Validation
validation_result = wt.run()
print(validation_result['success'])

# Persist Monitoring Setup and Results
db_service = DbServices(dw_backend_db_url)
db_service.create_tables()
db_service.add_watchtower(wt)
db_service.save_result(wt, validation_result)
db_service.update_watchtower_success_status(wt)
```

