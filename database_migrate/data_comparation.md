# Migration Data Comparation
## Update
Table var_option:
    option is reserved in the mysql, therefore, I changed:
    
        option —> options

## Comparation Table

 Table Name       | DB Type | Records
------------------|---------| -----
alembic_version   |sqlite   | 1
                  | mysql   | 1
article_metadata  | sqlite  | 33411
						 | mysql   | 33411
article_queue     | sqlite  | **41766**
						 | mysql   | **41763**
code_first_pass   | sqlite  | **161718**
						 | mysql   | **161712**
coder_second_pass | sqlite  | 33809
						 | mysql   | 33809
event             | sqlite  | 4864
					    | mysql   | 4864
second_pass_queue | sqlite  | 6142
                  | mysql   | 6142
user              | sqlite  | 38
                  | mysql   | 38
var_option        | sqlite  | 48
                  | mysql   | 48


