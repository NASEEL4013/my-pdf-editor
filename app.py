import os
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import io
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def split_pdf_by_custom_pages(input_stream, page_ranges):
    try:
        reader = PdfReader(input_stream)
        total_pages = len(reader.pages)
        print(f"총 페이지 수: {total_pages} 페이지")

        print(f"지정된 페이지들을 개별 PDF 파일로 분할합니다: {page_ranges}")
        
        split_files = [] 

        for item in page_ranges:
            writer = PdfWriter()
            pages_to_extract = []

            if isinstance(item, int):
                page_num_one_based = item
                if 1 <= page_num_one_based <= total_pages:
                    pages_to_extract.append(page_num_one_based - 1)
                else:
                    print(f"경고: {page_num_one_based} 페이지는 존재하지 않습니다. 건너뜁니다.")
            elif isinstance(item, str) and '-' in item:
                try:
                    start, end = map(int, item.split('-'))
                    if 1 <= start <= end <= total_pages:
                        for page_num in range(start - 1, end):
                            pages_to_extract.append(page_num)
                    else:
                        print(f"경고: 페이지 범위 '{item}'이 유효하지 않거나 PDF 범위를 벗어납니다. 건너뜁니다.")
                except ValueError:
                    print(f"경고: 잘못된 페이지 범위 형식 '{item}'입니다. (예: '10-12'). 건너뜁니다.")
            else:
                print(f"경고: 알 수 없는 페이지 지정 형식 '{item}'입니다. 건너뜁니다.")
            
            if pages_to_extract:
                for page_index in pages_to_extract:
                    writer.add_page(reader.pages[page_index])
                
                output_stream = io.BytesIO()
                writer.write(output_stream)
                output_stream.seek(0)
                split_files.append(output_stream)
                print(f"-> 지정된 페이지에 대한 파일 생성 완료.")
        
        return split_files

    except Exception as e:
        print(f"PDF 분할 중 오류 발생: {e}")
        return []


# 메인 페이지 (홈페이지)
@app.route('/')
def home():
    return render_template('index.html')

# PDF 분할기 페이지
@app.route('/pdf_splitter')
def pdf_splitter_page():
    return render_template('pdf_splitter.html')

# PDF 분할 요청을 처리하는 엔드포인트
@app.route('/split', methods=['POST'])
def split_pdf():
    if 'pdf_file' not in request.files:
        return "파일이 없습니다."
    
    pdf_file = request.files['pdf_file']
    
    if pdf_file.filename == '':
        return "파일을 선택해 주세요."
    
    page_ranges_str = request.form.get('page_ranges', '')
    if not page_ranges_str:
        return "페이지 범위를 입력해 주세요."
    
    page_ranges_list = [item.strip() for item in page_ranges_str.split(',')]
    
    if pdf_file:
        file_stream = pdf_file.read()
        split_files = split_pdf_by_custom_pages(io.BytesIO(file_stream), page_ranges_list)
        
        if split_files:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, file_stream in enumerate(split_files):
                    file_stream.seek(0)
                    zip_file.writestr(f"split_part_{i+1}.pdf", file_stream.read())
            
            zip_buffer.seek(0)
            
            return send_file(zip_buffer, as_attachment=True, download_name='split_pdfs.zip', mimetype='application/zip')
        else:
            return "PDF 분할에 실패했거나 유효한 페이지가 없습니다.", 400

    return "알 수 없는 오류가 발생했습니다.", 500

if __name__ == '__main__':
    app.run()