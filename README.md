# How to Run the Server Locally Using Anvil

## Disclaimer
Our current working directory is react-frontend. As Meky demonstrated during the meeting two weeks ago, the frontend UI has been improved significantly. We are currently in the process of integrating the Neo4j database, which represents the first major step in this phase of development.

* Before proceeding with the integration, follow the step-by-step instructions below to launch the application locally. *

1. Navigate to the Anvil dashboard (https://ondemand.anvil.rcac.purdue.edu/pun/sys/dashboard), then go to My Interactive Sessions.

2. Set up and launch a virtual machine environment. This session typically provides approximately 1.5 hours of access.

3. Once the environment is running, complete the login process to GitHub.

4. Install the required dependencies by following the standard npm setup steps (e.g., npm install). Ensure that Node.js is updated so the environment matches the expected configuration.

5. Launch the application using npm run dev. You should now be able to see the server running locally. This avoids the proxy-related blocking behavior encountered when running the app through Jupyter Notebook.
