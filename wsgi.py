from flaskServer import app
import ssl
if __name__=="__main__":
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    # ssl_context.load_cert_chain(certfile='STAR.kakao.golf.crt', keyfile='STAR.kakao.golf.key', password='kakaovx1!')

    app.run(debug=True, host='0.0.0.0', port=5000)#, ssl_context=ssl_context) 
