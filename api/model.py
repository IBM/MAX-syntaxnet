from flask import abort
from flask_restplus import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage

from config import MODEL_META_DATA
from core.backend import ModelWrapper

api = Namespace('model', description='Model information and inference operations')

model_meta = api.model('ModelMetadata', {
    'id': fields.String(required=True, description='Model identifier'),
    'name': fields.String(required=True, description='Model name'),
    'description': fields.String(required=True, description='Model description'),
    'license': fields.String(required=False, description='Model license')
})

@api.route('/metadata')
class Model(Resource):
    @api.doc('get_metadata')
    @api.marshal_with(model_meta)
    def get(self):
        '''Return the metadata associated with the model'''
        return MODEL_META_DATA


label_prediction = api.model('LabelPrediction', {
    'index': fields.String(required=False, description='Labels ranked by highest score'),
    'caption': fields.String(required=True, description='Caption generated by image'),
    'probability': fields.Float(required=True)
})

predict_response = api.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'predictions': fields.List(fields.Nested(label_prediction), description='Predicted labels and probabilities')
})

# set up parser for image input data
image_parser = api.parser()
image_parser.add_argument('image', type=FileStorage, location='files', required=True)

@api.route('/predict')
class Predict(Resource):

    model_wrapper = ModelWrapper()

    @api.doc('predict')
    @api.expect(image_parser)
    @api.marshal_with(predict_response)
    def post(self):
        '''Make a prediction given input data'''
        result = {'status': 'error'}

        args = image_parser.parse_args()

        if not args['image'].mimetype.endswith(('jpg', 'jpeg', 'png')):
            abort(400, 'Invalid file type/extension. Please provide an image in JPEG or PNG format.')

        image_data = args['image'].read()
        preds = self.model_wrapper.predict(image_data)

        label_preds = [{'index': p[0], 'caption': p[1], 'probability': p[2]} for p in [x for x in preds]]
        result['predictions'] = label_preds
        result['status'] = 'ok'

        return result
