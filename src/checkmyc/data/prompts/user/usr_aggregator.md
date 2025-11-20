# User Prompt
You are given input comments grouped by topic.  
Each comment is provided in the form:

```
{ "id": "ID###", "text": "comment text" }
```

Cluster the comments by semantic similarity following the system rules.  
Return ONLY the JSON output required.

**Input:**

{{ comments }}