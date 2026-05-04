import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

df = pd.read_csv("Metro_Manila_Catholic_Churches_2020.csv", encoding="latin-1")
df_cities = df.iloc[1:].copy()

X = df_cities[['Household Population']]
y = df_cities['Roman Catholic, excluding Catholic Charismatics']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

plt.figure(figsize=(10, 6))

plt.scatter(X_train, y_train, color='blue', label='Training Data', alpha=0.7)
plt.scatter(X_test, y_test, color='red', label='Testing Data', s=60)

plt.plot(X, model.predict(X), color='green', linewidth=2, label='Regression Line')

plt.xlabel("Total Household Population")
plt.ylabel("Number of Roman Catholics")
plt.title("Linear Regression: Population vs Roman Catholics in Metro Manila (2020)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)

plt.savefig("linear_regression_population_catholics.png")

print("Coefficient (slope):", model.coef_[0])
print("Intercept:", model.intercept_)