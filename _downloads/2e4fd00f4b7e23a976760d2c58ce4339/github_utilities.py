# This file contains utility functions using the github API via github-python:
# https://github.com/PyGithub/PyGithub (licensed LGPL3)
#
# All functions must have a proper docstring, because we are using them as tools for function calling using LLMs.
# Most of the code in this file has been written using bia-bob 
import os
import github
from github import Github
import bia_bob

def list_issues(repository:str, state:str="open")->dict:
    """List all github issues with defined state on a specified repository.

    Parameters
    ----------
    repository:str
        a github repository
    state:str, optional
        issue status: can be "open", "closed" or "all"

    Returns
    -------
        dictionary of issues
    """
    from github import Github

     # Initialize Github client
    GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
    g = Github(GITHUB_API_KEY)
    
    # Get the repository
    repo = g.get_repo(repository)
    
    # Fetch all open issues
    issues = repo.get_issues(state=state)

    result = {}
    # Print open issues
    for issue in issues:
        result[issue.number] = issue.title

    return result

def get_github_issue_details(repository: str, issue: int) -> str:
    """Retrieve detailed information about a specific GitHub issue.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository (e.g., "username/repo-name").
    issue : int
        The issue number to retrieve details for.

    Returns
    -------
    str
    """
    GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
    g = Github(GITHUB_API_KEY)
    
    # Get the repository
    repo = g.get_repo(repository)

    # Fetch the specified issue
    issue = repo.get_issue(number=issue)

    # Format issue details
    content = f"""Issue #{issue.number}: {issue.title}
State: {issue.state}
Created at: {issue.created_at}
Updated at: {issue.updated_at}
Closed at: {issue.closed_at}
Author: {issue.user.login}
Assignees: {', '.join([assignee.login for assignee in issue.assignees])}
Labels: {', '.join([label.name for label in issue.labels])}
Comments: {issue.comments}
Body:
{issue.body}"""

    # Add comments if any
    if issue.comments > 0:
        content += "\n\nComments:"
        comments = issue.get_comments()
        for comment in comments:
            content += f"\n\nComment by {comment.user.login} on {comment.created_at}:\n{comment.body}"

    return content




def list_repository_files(repo_name: str) -> list:
    """
    List all files in a given GitHub repository.

    This function uses the GitHub API to retrieve and list all files
    in the specified repository.

    Parameters
    ----------
    repo_name : str
        The full name of the GitHub repository (e.g., "username/repo-name").

    Returns
    -------
    list
        A list of strings, where each string is the path of a file in the repository.
    """
    from github import Github
    
    # Initialize Github client
    GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
    g = Github(GITHUB_API_KEY)
    
    # Get the repository
    repo = g.get_repo(repo_name)

    # Get all contents of the repository
    contents = repo.get_contents("")
    
    # List to store all file paths
    all_files = []

    # Iterate through all contents
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            # If it's a directory, get its contents and add them to the list
            contents.extend(repo.get_contents(file_content.path))
        else:
            # If it's a file, add its path to the list
            all_files.append(file_content.path)

    return all_files



def get_repository_file_contents(repo_name: str, file_paths: list) -> dict:
    """
    Retrieve the contents of specified files from a GitHub repository.

    Parameters
    ----------
    repo_name : str
        The full name of the GitHub repository (e.g., "username/repo-name").
    file_paths : list
        A list of file paths within the repository to retrieve the contents of.

    Returns
    -------
    dict
        A dictionary where keys are file paths and values are the contents of the files.
    """
    from github import Github
    
    # Initialize Github client
    GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
    g = Github(GITHUB_API_KEY)
    
    # Get the repository
    repo = g.get_repo(repo_name)

    # Dictionary to store file contents
    file_contents = {}

    # Iterate through the file paths
    for file_path in file_paths:
        try:
            # Get the file content
            file_content = repo.get_contents(file_path)
            
            # Decode and store the content
            file_contents[file_path] = file_content.decoded_content.decode()
            
        except Exception as e:
            file_contents[file_path] = f"Error accessing {file_path}: {str(e)}"

    return file_contents


def update_file_in_new_branch(repository, file_path, new_content):
    """Modifies a specified file with new content and saves the changes in a new git branch. 
    The name of the new branch is returned.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository (e.g., "username/repo-name")
    file_paths : str
        A file path within the repository to change the contents of.
    new_conent : str
        Text content that should be written into the file. 

    Returns
    -------
    str
        The name of the brach where the change file is stored.
    """
    from github import Github
    import os
    import random
    import string

    #print(f'update_file_in_new_branch(repository="{repository}", file_path="{file_path}", new_content="{new_content}"')
    
    # Authenticate with GitHub
    GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
    g = Github(GITHUB_API_KEY)
    
    # Get the repository
    repo = g.get_repo(repository)
    
    # Get the main branch
    main_branch = repo.get_branch("main")

    # access the file
    file = repo.get_contents(file_path)

    # Create a new branch
    new_branch_name = "mod-" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha)
        
    # Commit the changes
    repo.update_file(file.path, "Update file content", new_content, file.sha, branch=new_branch_name)

    return new_branch_name


def send_pull_request(repository, branch_name, title, description):
    """Create a pull request from a defined branch into the main branch.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository (e.g., "username/repo-name")
    branch_name : str
        The name of the branch that should be merged into main.
    title : str
        A one-liner explaining what was changed in the branch
    description : str
        A more detailed description of what has happened. 
        If the changes are related to an issue write "closes #99 " 
        where 99 stands for the issue number the pull-request is related to.

    Returns
    -------
    str
        The url to the pull-request that was just created.
    """
    from github import Github
    import os
    import random
    import string
    
    # Authenticate with GitHub
    GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
    g = Github(GITHUB_API_KEY)
    
    # Get the repository
    repo = g.get_repo(repository)
    
    # Create a pull request
    pr = repo.create_pull(title=title, body=description, head=branch_name, base="main")
    
    return f"Pull request created: {pr.html_url}"

