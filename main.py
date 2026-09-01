from app.rag_pipeline import run_rag


def main():

    query = input("Ask: ")

    answer = run_rag(query)

    print("\n--- ANSWER ---\n")
    print(answer)


if __name__ == "__main__":
    main()