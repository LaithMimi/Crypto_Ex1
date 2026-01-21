import pypdf

def read_pdf():
    try:
        reader = pypdf.PdfReader('../ex3.pdf')
        print(f"Total Pages: {len(reader.pages)}")
        for i, page in enumerate(reader.pages):
            print(f"--- PAGE {i+1} ---")
            print(page.extract_text())
            print("\n")
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    read_pdf()
