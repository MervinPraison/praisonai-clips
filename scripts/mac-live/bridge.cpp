// Experimental in-process Qt control bridge. Loaded only into our isolated app copy.
#include <QtCore/QCoreApplication>
#include <QtCore/QJsonDocument>
#include <QtCore/QJsonArray>
#include <QtCore/QJsonObject>
#include <QtCore/QMetaMethod>
#include <QtCore/QMetaProperty>
#include <QtCore/QPointer>
#include <QtCore/QTimer>
#include <QtCore/QFile>
#include <QtCore/QRectF>
#include <QtCore/QAbstractItemModel>
#include <QtCore/QAbstractProxyModel>
#include <QtCore/QBuffer>
#include <QtWidgets/QApplication>
#include <QtWidgets/QWidget>
#include <QtWidgets/QAbstractItemView>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QTabWidget>
#include <QtGui/QAction>
#include <QtWidgets/QUndoView>
#include <QtGui/QUndoStack>
#include <QtNetwork/QTcpServer>
#include <QtNetwork/QTcpSocket>
#include <thread>
#include <chrono>

static QHash<quintptr,QPointer<QObject>> objects;
static QJsonObject describe(QObject *o) {
    quintptr id=reinterpret_cast<quintptr>(o); objects[id]=o;
    if(o->parent())objects[reinterpret_cast<quintptr>(o->parent())]=o->parent();
    return {{"id",QString::number(id,16)},{"class",o->metaObject()->className()},
            {"name",o->objectName()},{"parent",o->parent()?QString::number(reinterpret_cast<quintptr>(o->parent()),16):QString()}};
}
static void visit(QObject *o, QJsonArray &out, const QString &match, QSet<QObject*> &seen) {
    if (!o || seen.contains(o)) return; seen.insert(o);
    if (QString(o->metaObject()->className()).contains(match,Qt::CaseInsensitive) || o->objectName().contains(match,Qt::CaseInsensitive)) out.append(describe(o));
    for (QObject *c:o->children()) visit(c,out,match,seen);
    if(auto *w=qobject_cast<QWidget*>(o))for(QAction *a:w->actions())visit(a,out,match,seen);
    if(auto *b=qobject_cast<QToolButton*>(o))visit(b->defaultAction(),out,match,seen);
}
static QJsonObject dispatch(const QJsonObject &r) {
    QString op=r["op"].toString();
    if(op=="ping")return {{"ok",true},{"pid",QCoreApplication::applicationPid()},{"application",QCoreApplication::applicationName()},{"version",QCoreApplication::applicationVersion()}};
    if(op=="objects") {
        QJsonArray out; QSet<QObject*> seen;
        visit(qApp,out,r["match"].toString(),seen);
        for(QWidget *w:QApplication::topLevelWidgets()) visit(w,out,r["match"].toString(),seen);
        return {{"ok",true},{"objects",out}};
    }
    QObject *o=objects.value(r["id"].toString().toULongLong(nullptr,16));
    if(!o) return {{"ok",false},{"error","Object no longer exists; rediscover it"}};
    if(op=="inspect") {
        QJsonObject props; QJsonArray methods;
        for(int i=0;i<o->metaObject()->propertyCount();++i){auto p=o->metaObject()->property(i);props[p.name()]=QJsonValue::fromVariant(p.read(o));}
        for(int i=0;i<o->metaObject()->methodCount();++i){auto m=o->metaObject()->method(i);if(m.methodType()!=QMetaMethod::Signal)methods.append(QString::fromLatin1(m.methodSignature()));}
        auto result=describe(o);result["ok"]=true;result["properties"]=props;result["methods"]=methods;
        if(auto *v=qobject_cast<QAbstractItemView*>(o))if(v->model())result["model"]=describe(v->model());
        if(auto *v=qobject_cast<QAbstractProxyModel*>(o))if(v->sourceModel())result["sourceModel"]=describe(v->sourceModel());
        if(auto *v=qobject_cast<QUndoView*>(o))if(v->stack())result["stack"]=describe(v->stack());
        if(auto *v=qobject_cast<QTabWidget*>(o)){QJsonArray tabs;for(int i=0;i<v->count();++i)tabs.append(QJsonObject{{"index",i},{"title",v->tabText(i)},{"widget",describe(v->widget(i))}});result["tabs"]=tabs;}
        return result;
    }
    if(op=="rows") {
        auto *model=qobject_cast<QAbstractItemModel*>(o);if(!model)return {{"ok",false},{"error","Not a model"}};
        QModelIndex parent;
        for(auto row:r["parent"].toArray())parent=model->index(row.toInt(),0,parent);
        QJsonArray rows;auto roles=model->roleNames();roles.insert(Qt::DisplayRole,"display");
        for(int row=0;row<qMin(model->rowCount(parent),1000);++row){QJsonObject entry;auto index=model->index(row,0,parent);entry["row"]=row;entry["children"]=model->rowCount(index);for(auto it=roles.begin();it!=roles.end();++it)entry[QString::fromUtf8(it.value())]=QJsonValue::fromVariant(model->data(index,it.key()));rows.append(entry);}
        return {{"ok",true},{"rows",rows}};
    }
    if(op=="capture") {
        auto *w=qobject_cast<QWidget*>(o);if(!w)return {{"ok",false},{"error","Not a widget"}};
        QByteArray bytes;QBuffer buffer(&bytes);buffer.open(QIODevice::WriteOnly);w->grab().save(&buffer,"PNG");
        return {{"ok",true},{"png",QString::fromLatin1(bytes.toBase64())}};
    }
    if(op=="invoke") {
        QByteArray sig=QMetaObject::normalizedSignature(r["method"].toString().toUtf8());
        int ix=o->metaObject()->indexOfMethod(sig);
        if(ix<0)return {{"ok",false},{"error","No such native method"}};
        QMetaMethod m=o->metaObject()->method(ix);
        if(m.methodType()==QMetaMethod::Signal)return {{"ok",false},{"error","Signal invocation is disabled"}};
        QJsonArray args=r["args"].toArray();
        if(args.size()!=m.parameterCount() || args.size()>10)return {{"ok",false},{"error","Argument count mismatch"}};
        QVariant vals[10];QGenericArgument generic[10];
        for(int i=0;i<args.size();++i){
            auto type=m.parameterMetaType(i);
            if(type==QMetaType::fromType<QRectF>()) {auto a=args[i].toArray();if(a.size()!=4)return {{"ok",false},{"error","QRectF requires [x,y,width,height]"}};vals[i]=QRectF(a[0].toDouble(),a[1].toDouble(),a[2].toDouble(),a[3].toDouble());}
            else if(type==QMetaType::fromType<QList<int>>()){QList<int> list;for(auto v:args[i].toArray())list.append(v.toInt());vals[i]=QVariant::fromValue(list);}
            else {vals[i]=args[i].toVariant(); if(type!=QMetaType::fromType<QVariant>() && !vals[i].convert(type))return {{"ok",false},{"error","Cannot convert argument"}};}
            generic[i]=QGenericArgument(type.name(),type==QMetaType::fromType<QVariant>()?&vals[i]:vals[i].constData());
        }
        auto rt=m.returnMetaType();QVariant result(rt);QGenericReturnArgument ret;
        if(rt.id()!=QMetaType::Void)ret=QGenericReturnArgument(rt.name(),result.data());
        bool ok=m.invoke(o,Qt::DirectConnection,ret,generic[0],generic[1],generic[2],generic[3],generic[4],generic[5],generic[6],generic[7],generic[8],generic[9]);
        return {{"ok",ok},{"result",QJsonValue::fromVariant(result)}};
    }
    return {{"ok",false},{"error","Unknown operation"}};
}
static void startBridge() {
    auto *server=new QTcpServer(qApp);
    QByteArray token=qgetenv("PRAISON_KDENLIVE_TOKEN");
    if(token.size()<32 || !server->listen(QHostAddress::LocalHost,qEnvironmentVariableIntValue("PRAISON_KDENLIVE_PORT"))) return;
    QObject::connect(server,&QTcpServer::newConnection,server,[server,token] {
        while(server->hasPendingConnections()){
            auto *s=server->nextPendingConnection();auto buffer=std::make_shared<QByteArray>();
            QTimer::singleShot(10000,s,[s]{s->disconnectFromHost();});
            QObject::connect(s,&QTcpSocket::disconnected,s,&QObject::deleteLater);
            QObject::connect(s,&QTcpSocket::readyRead,s,[s,buffer,token]{
                *buffer+=s->readAll();if(buffer->size()>1048576){s->disconnectFromHost();return;}
                int end=buffer->indexOf("\r\n\r\n");if(end<0)return;
                auto lines=buffer->left(end).split('\n');int length=-1;bool authorized=false;
                for(auto line:lines){line=line.trimmed();if(line.toLower().startsWith("content-length:"))length=line.mid(15).trimmed().toInt();if(line.startsWith("Authorization: Bearer "))authorized=line.mid(22)==token;}
                if(length<0 || buffer->size()<end+4+length)return;
                QJsonObject out;
                if(!authorized)out={{"ok",false},{"error","Unauthorized"}};
                else {QJsonParseError error;auto doc=QJsonDocument::fromJson(buffer->mid(end+4,length),&error);out=error.error==QJsonParseError::NoError && doc.isObject()?dispatch(doc.object()):QJsonObject{{"ok",false},{"error","Expected JSON object"}};}
                QByteArray body=QJsonDocument(out).toJson(QJsonDocument::Compact);
                s->write("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: "+QByteArray::number(body.size())+"\r\n\r\n"+body);s->disconnectFromHost();
            });
        }
    });
}
__attribute__((constructor)) static void bootstrap() {
    // Media workers must not inherit the editor-only bridge.
    unsetenv("DYLD_INSERT_LIBRARIES");
    std::thread([]{
        for(int i=0;i<600;++i){
            if(auto *app=QCoreApplication::instance()) {QMetaObject::invokeMethod(app,[]{QTimer::singleShot(3000,qApp,startBridge);},Qt::QueuedConnection);return;}
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }).detach();
}
