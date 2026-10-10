from volunteer_signup.app.factory import launch

if __name__ == "__main__":
    app = launch()
    app.run(debug=True, port=5000)
