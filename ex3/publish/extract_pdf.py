import pypdf

def read_pdf():
    try:
        reader = pypdf.PdfReader('../ex3.pdf')
        with open('ex3_content.txt', 'w', encoding='utf-8') as f:
            for i, page in enumerate(reader.pages):
                f.write(f"--- PAGE {i+1} ---\n")
                f.write(page.extract_text())
                f.write("\n\n")
        print("PDF content written to ex3_content.txt")
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    read_pdf()
