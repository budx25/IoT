import argparse
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import math

def main(input_csv, out_model, random_state=42):
    df = pd.read_csv(input_csv)
    df['ldr_ma5'] = df['ldr_value'].rolling(5, min_periods=1).mean()
    X = df[['ldr_value', 'ldr_ma5']].fillna(0).values
    y = df['servo_angle'].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=random_state)
    model = RandomForestRegressor(n_estimators=100, random_state=random_state)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    mse = mean_squared_error(y_test, preds)           
    rmse = math.sqrt(mse)                             
    print(f"MAE: {mae:.3f}, RMSE: {rmse:.3f}")

    joblib.dump(model, out_model)
    print(f"Model saved to {out_model}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="ldr_servo_dataset.csv")
    parser.add_argument("--out", default="model_joblib.pkl")
    args = parser.parse_args()
    main(args.input, args.out)