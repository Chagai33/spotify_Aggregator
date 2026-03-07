import os
import glob

# Search for python files in views/ and app.py
files_to_check = glob.glob("c:/Users/Administrator/Documents/spotify_Aggregator/views/*.py")
files_to_check.append("c:/Users/Administrator/Documents/spotify_Aggregator/app.py")

for file_path in files_to_check:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace the deprecated parameter
    # Wait: Streamlit documentation (and error logs) says: 
    # For `use_container_width=True`, use `width='stretch'` or `use_container_width=False`, use `width='content'`.
    # Wait, some methods like st.button may not accept width yet in older versions. 
    # For st.dataframe, replacing use_container_width=True with width="stretch" is recommended.
    # Note: I'll replace st.dataframe(..., use_container_width=True) to st.dataframe(..., use_container_width=True) 
    # Let me re-read the error out: "Please replace `use_container_width` with `width`. ... For `use_container_width=True`, use `width='stretch'`."
    # Since it's string replace:
    new_content = content.replace("use_container_width=True", "width=\"stretch\"")
    new_content = new_content.replace("use_container_width=False", "width=\"content\"")
    
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated: {file_path}")

print("Cleanup script complete.")
