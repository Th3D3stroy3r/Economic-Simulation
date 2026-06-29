from backend import WorldEconomyAPI, DatabaseConfig
from tablesturningUI import UI
def main(): #Kumbalaya motherhucker
    config = DatabaseConfig()
    api = WorldEconomyAPI(config)
    app = UI(api)
    app.root.mainloop()
if __name__ == "__main__":
    main()