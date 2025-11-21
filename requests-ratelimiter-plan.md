# Rate Limiting Options for requests.get()

You have a few options for pausing between `requests.get()` calls:

## Option 1: Simple `time.sleep()` (Quick Solution)

Add delays using Python's built-in `time` module:

```python
import time
from rich import print as rprint
import requests

# ... in your loop:
for folder in folders:
    service_folder_url = f"https://apps.fs.usda.gov/arcx/rest/services/{folder}?f=pjson"
    service_folder_resp = requests.get(service_folder_url)
    time.sleep(0.5)  # Pause 0.5 seconds between requests

    # ... rest of your code
```

## Option 2: Use `requests-ratelimiter` (Already Installed)

Since you already have `requests-ratelimiter` in your dependencies, you can use it for more sophisticated rate limiting:

```python
from requests_ratelimiter import LimiterSession
from rich import print as rprint

# Create a session with rate limiting (e.g., 2 requests per second)
session = LimiterSession(per_second=2)

# Replace requests.get with session.get
resp = session.get(FS_SERVICES_INDEX_URL)
```

Then replace all `requests.get()` calls with `session.get()` throughout your code. This approach:
- Automatically handles rate limiting across all requests
- Queues requests if you exceed the limit
- Is more robust than manual sleep calls

## Recommendation

For your use case (fetching from USDA Forest Service API), I'd suggest using `requests-ratelimiter` with a conservative rate like `per_second=2` or `per_second=1` to be respectful of the API server.
