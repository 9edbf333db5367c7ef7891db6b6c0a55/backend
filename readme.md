# HashTag: 9edbf333db5367c7ef7891db6b6c0a55

Everything, Everyday.

### Starting the developer environment

##### Initialise the Google Datastore Emulator:

```bash
gcloud beta emulators datastore start
```

##### App serving

```python
dev_appserver.py --clear_datastore=yes app.yaml
```
